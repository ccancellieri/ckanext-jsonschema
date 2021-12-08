import ckan.plugins as plugins
import ckan.lib.helpers as h
import ckan.plugins.toolkit as toolkit
_ = toolkit._

from ckan.common import c
import json

import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.validators as _v
import ckanext.jsonschema.blueprints as _b
import ckanext.jsonschema.interfaces as _i

get_validator = toolkit.get_validator
not_missing = get_validator('not_missing')
not_empty = get_validator('not_empty')
resource_id_exists = get_validator('resource_id_exists')
package_id_exists = get_validator('package_id_exists')
ignore_missing = get_validator('ignore_missing')
empty = get_validator('empty')
boolean_validator = get_validator('boolean_validator')
int_validator = get_validator('int_validator')
OneOf = get_validator('OneOf')
isodate = get_validator('isodate')


convert_to_extras = toolkit.get_converter('convert_to_extras')
convert_from_extras = toolkit.get_converter('convert_from_extras')


import uuid
import ckan.lib.navl.dictization_functions as df

    # let's grab the default schema in our plugin
from ckan.logic.schema import \
    default_create_package_schema,\
    default_update_package_schema,\
    default_show_package_schema,\
    default_group_schema,\
    default_tags_schema

import logging
log = logging.getLogger(__name__)

from ckan.plugins import PluginImplementations


# check IConfigurer
HANDLED_DATASET_TYPES = []
HANDLED_RESOURCES_TYPES = {}

def handled_resource_types(dataset_type, opt=_c.SCHEMA_OPT, version=_c.SCHEMA_VERSION, renew = False):

    if HANDLED_RESOURCES_TYPES and not renew:
        return HANDLED_RESOURCES_TYPES.get(dataset_type)

    supported_resource_types = []
    for plugin in _v.JSONSCHEMA_PLUGINS:
        try:
            supported_resource_types.extend(plugin.supported_resource_types(dataset_type, opt, version))
        except Exception as e:
            log.error('Error resolving resource json types for dataset type: {}\n{}'.format(dataset_type,str(e)))
    
    for type in supported_resource_types:
        if type not in _c.JSON_CATALOG[_c.JSON_SCHEMA_KEY].keys():
            raise Exception('Error resolving resource json schema for type:\n{}'.format(type))
    
    HANDLED_RESOURCES_TYPES.update({dataset_type:supported_resource_types})

    return supported_resource_types

def handled_dataset_types(opt=_c.SCHEMA_OPT, version=_c.SCHEMA_VERSION, renew = False):
    '''
    #TODO
    defines a list of dataset types that
    this plugin handles. Each dataset has a field containing its type.
    Plugins can register to handle specific types of dataset and ignore
    others. Since our plugin is not for any specific type of dataset and
    we want our plugin to be the default handler, we update the plugin
    code to contain the following:
    '''
    if HANDLED_DATASET_TYPES and not renew:
        return HANDLED_DATASET_TYPES
    
    # This plugin doesn't handle any special package types, it just
    # registers itself as the default (above).
    supported_dataset_types = []
    for plugin in _v.JSONSCHEMA_PLUGINS:
        try:
            supported_dataset_types.extend(plugin.supported_dataset_types(opt, version))
        except Exception as e:
            log.error('Error resolving dataset types:\n{}'.format(str(e)))
    
    for type in supported_dataset_types:
        if type not in _c.JSON_CATALOG[_c.JSON_SCHEMA_KEY].keys():
            raise Exception('Error resolving dataset json schema for type:\n{}'.format(type))

    return supported_dataset_types

class JsonschemaPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions)

    #IActions
    def get_actions(self):
        from ckanext.jsonschema.logic.actions import importer
        actions = {
            'jsonschema_importer': importer
        }
        return actions

    # IBlueprint
    
    def get_blueprint(self):
        return _b.jsonschema
    
    # ITemplateHelpers

    def get_helpers(self):
        return {
            'jsonschema_get_body_key': lambda : _c.SCHEMA_BODY_KEY,
            'jsonschema_get_type_key': lambda : _c.SCHEMA_TYPE_KEY,
            'jsonschema_get_opt_key': lambda : _c.SCHEMA_OPT_KEY,
            'jsonschema_get_version_key': lambda : _c.SCHEMA_VERSION_KEY,

            # 'jsonschema_get_body': lambda d_id, r_id = None : _t.get_body(d_id, r_id),
            # 'jsonschema_get_type': lambda d_id, r_id = None : _t.get_type(d_id, r_id),
            # 'jsonschema_get_opt': lambda d_id, r_id = None : _t.get_opt(d_id, r_id),
            # 'jsonschema_get_version': lambda d_id, r_id = None : _t.get_version(d_id, r_id),

            'jsonschema_get_dataset_body': lambda d = None : _t.as_dict(_t.get_dataset_body(d)),
            'jsonschema_get_dataset_type': lambda d : _t.get_dataset_type(d),
            'jsonschema_get_dataset_opt': lambda d : _t.as_dict(_t.get_dataset_opt(d)),
            'jsonschema_get_dataset_version': lambda d : _t.get_dataset_version(d),

            'jsonschema_get_resource': lambda r = None : _t.get(r),
            'jsonschema_get_resource_body': lambda r = None : _t.as_dict(_t.get_resource_body(r)),
            'jsonschema_get_resource_type': lambda r : _t.get_resource_type(r),
            'jsonschema_get_resource_opt': lambda r : _t.as_dict(_t.get_resource_opt(r)),
            'jsonschema_get_resource_version': lambda r : _t.get_resource_version(r),

            'jsonschema_get_schema': lambda x : json.dumps(_t.get_schema_of(x)),
            'jsonschema_get_template': lambda x : json.dumps(_t.get_template_of(x)),
            'jsonschema_get_dataset_type': _t.get_dataset_type, #TODO
            'jsonschema_resolve_extras': _t.resolve_extras,
            'jsonschema_resolve_resource_extras': _t.resolve_resource_extras,

            'jsonschema_handled_resource_types': handled_resource_types,
            'jsonschema_handled_dataset_types': handled_dataset_types,
            # 'jsonschema_get_runtime_opt': lambda x : json.dumps(_t.get_opt_of(x)),
        }


    # IPackageController

    # def before_index(self, pkg_dict):
    #     # return pkg_dict
    #     # d=pkg_dict

    #     # d.pop('_version_')

    #     pkg_dict.update({'validated_data_dict': json.loads(pkg_dict)})
        
    #     return pkg_dict
        # # TODO solr
        # return {
        #     'title':d.title,
        #     'name':d.name,
        #     'url':d.url
        # }
            

    # def before_view(self, pkg_dict):
    #     '''
    #     Extensions will recieve this before the dataset
    #     gets displayed. The dictionary passed will be
    #     the one that gets sent to the template.
    #     '''
    #     pass


    # def _opt_map(self, opt = _c.SCHEMA_OPT, version = _c.SCHEMA_VERSION):
    #     for plugin in _v.JSONSCHEMA_PLUGINS:
    #         try:
    #             opt.update(plugin.opt_map(opt, version))
    #         except Exception as e:
    #             log.error('Error resolving dataset types:\n{}'.format(str(e)))
    #     return opt
    
    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'ckanext-jsonschema')

        # Append all the rest of the available schemas
        _c.JSON_CATALOG.update({
                    _c.JSON_SCHEMA_KEY:_t.read_all_schema(),
                    _c.JSON_TEMPLATE_KEY:_t.read_all_template(),
                    _c.JS_MODULE_KEY:_t.read_all_module()
            })
        
        HANDLED_DATASET_TYPES = handled_dataset_types(renew = True)

        HANDLED_RESOURCES_TYPES = {}
        for dataset_type in HANDLED_DATASET_TYPES:
            HANDLED_RESOURCES_TYPES.update({ dataset_type : handled_resource_types(dataset_type, renew = True) })

        # assert len(_c.JSON_CATALOG[_c.JSON_SCHEMA_KEY])==\
        #     len(_c.JSON_CATALOG[_c.JSON_TEMPLATE_KEY])
    
        
    # IValidators

    def get_validators(self):

        return {
            u'jsonschema_is_valid': _v.schema_check,
        }

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return False


    # IDatasetForm
    ##############

    def package_types(self):
        return handled_dataset_types()

    # def setup_template_variables(self, context, data_dict):
        # # TODO: https://github.com/ckan/ckan/issues/6518
        # path = c.environ['CKAN_CURRENT_URL']
        # type = path.split('/')[1]
        # jsonschema = {
        #     # 'data_dict' : data_dict
        # }
        # c.jsonschema = jsonschema
        # return jsonschema

    # def new_template(self):
    #     return 'package/new.html'

    # # TODO: https://github.com/ckan/ckan/issues/6518 (related but available on 2.9.x)
    def read_template(self):
        return 'source/read.html'
    # def read_template(self):
        # for plugin in _v.JSONSCHEMA_PLUGINS:
        #     try:
        #         plugin.read_template()
        #         return
        #     except Exception as e:
        #         log.error('Error resolving dataset types:\n{}'.format(str(e)))

    # def edit_template(self):
    #     return 'package/edit.html'

    # def search_template(self):
    #     return 'package/search.html'

    # def history_template(self):
    #     return 'package/history.html'

    # def resource_template(self):
    #     return 'package/resource_read.html'

    # def package_form(self):
    #     return 'package/new_package_form.html'

    # def resource_form(self):
    #     return 'package/snippets/resource_form.html'

    # Updating the CKAN schema
    def create_package_schema(self):

        # schema = super(toolkit.DefaultDatasetForm, self).create_package_schema()
        schema = default_create_package_schema()

        return _modify_package_schema(schema)

    def update_package_schema(self):

        schema = default_update_package_schema()

        return _modify_package_schema(schema)

    # TODO presentation layer (solr also is related)
    # def show_package_schema(self):
    #     schema = default_show_package_schema()

    #     # TODO why?!?!? this has been fixed in scheming 
    #     # but core now is broken... :(
    #     for field in schema['resources'].keys():
    #         if isodate in schema['resources'][field]:
    #             schema['resources'][field].remove(isodate)

    #     # schema.get('__before').append(_v.resource_serializer)
    #     schema.get('__after', []).append(_v.serializer)
    #     return schema
        
def _modify_package_schema(schema):
    # insert in front

    before = schema.get('__before')
    if not before:
        before = []
        schema['__before'] = before

    before.insert(0, _v.resource_extractor)
    before.insert(0, _v.extractor)
    before.insert(0, _v.before_extractor)
    # the following will be the first...
    before.insert(0, _v.schema_check)
    return schema
