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


# check IConfigurer
HANDLED_DATASET_TYPES = []
HANDLED_RESOURCES_TYPES = {}

TYPE_JSONSCHEMA='jsonschema'

class JsonschemaPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(_i.IBinder, inherit = True)

    # IBinder

    def get_opt(self, dataset_type, opt, version):
        opt.update(_c.SCHEMA_OPT)
        return opt

    def extract_from_json(self, body, type, opt, version, key, data, errors, context):
        # TODO which type schema or dataset?
        
        _data = df.unflatten(data)
        if key==('name',):
            name = str(body.get('name', uuid.uuid4()))
            name = name or _data.get('name') #TODO error if null...
            if not name:
                _v.stop_with_error('Unable to obtain {}'.format(key), key, errors)
                    
            _dict = {
                'name': name,
                'url': h.url_for(controller = 'package', action = 'read', id = name, _external = True),
            }
            data.update(df.flatten_dict(_dict))

        elif key==('title',):
            title = str(body.get('title', uuid.uuid4()))
            title = title or _data.get('title') #TODO error if null...
            if not title:
                _v.stop_with_error('Unable to obtain {}'.format(key), key, errors)
                    
            _dict = {
                'title': title
            }
            data.update(df.flatten_dict(_dict))

        # TODO notes

        data.update(df.flatten_dict(_dict))

    def supported_resource_types(self, dataset_type, opt=_c.SCHEMA_OPT, version=_c.SCHEMA_VERSION):
        if version != _c.SCHEMA_VERSION:
            # when version is not the default one we don't touch
            return []

        if dataset_type in _c.SUPPORTED_DATASET_FORMATS:
            #TODO should be a dic binding set of resources to dataset types 
            return _c.SUPPORTED_RESOURCE_FORMATS
        return []

    def supported_dataset_types(self, opt, version):
        if version != _c.SCHEMA_VERSION:
            # when version is not the default one we don't touch
            return []
        return _c.SUPPORTED_DATASET_FORMATS

    # IBlueprint
    def get_blueprint(self):
        return _b.jsonschema

    # IPackageController

    # def before_index(self, pkg_dict):
    #     '''
    #     Extensions will receive what will be given to the solr for indexing. This is essentially a flattened dict (except for multli-valued fields such as tags) of all the terms sent to the indexer. The extension can modify this by returning an altered version.
    #     '''
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

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'jsonschema_get_body_key': lambda : _c.SCHEMA_BODY_KEY,
            'jsonschema_get_type_key': lambda : _c.SCHEMA_TYPE_KEY,
            'jsonschema_get_opt_key': lambda : _c.SCHEMA_OPT_KEY,
            'jsonschema_get_version_key': lambda : _c.SCHEMA_VERSION_KEY,
            'jsonschema_get_schema': lambda x : json.dumps(_t.get_schema_of(x)),
            'jsonschema_get_template': lambda x : json.dumps(_t.get_template_of(x)),
            'jsonschema_get_dataset_type': _v.get_dataset_type,
            'jsonschema_resolve_extras': _v.resolve_extras,
            'jsonschema_resolve_resource_extras': _v.resolve_resource_extras,
            'jsonschema_handled_resource_types': handled_resource_types,
            'jsonschema_handled_dataset_types': handled_dataset_types,
            # 'jsonschema_get_runtime_opt': lambda x : json.dumps(_t.get_opt_of(x)),
        }

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

        '''
        Validators that need access to the database or information 
        about the user may be written as a callable taking two 
        parameters. context['session'] is the sqlalchemy session 
        object and context['user'] is the username of the logged-in 
        user:

        from ckan.plugins.toolkit import Invalid

        validator(key, flattened_data, errors, context)

        Validators that need to access or update multiple fields 
        may be written as a callable taking four parameters.

        All fields and errors in a flattened form are passed to 
        the validator. The validator must fetch values from 
        flattened_data and may replace values in flattened_data. 
        The return value from this function is ignored.

        key is the flattened key for the field to which this 
        validator was applied. For example ('notes',) for the 
        dataset notes field or ('resources', 0, 'url') for the 
        url of the first resource of the dataset. These flattened 
        keys are the same in both the flattened_data and errors 
        dicts passed.

        errors contains lists of validation errors for each field.

        context is the same value passed to the two-parameter 
        form above.

        Note that this form can be tricky to use because some 
        of the values in flattened_data will have had validators 
        applied but other fields won't. You may add this type of 
        validator to the special schema fields __before or 
        __after to have them run before or after all the other 
        validation takes place to avoid the problem of working 
        with partially-validated data.
        '''

        return {
            # u'equals_to_zero': lambda x : x==0,
            u'schema_is_valid': _v.schema_check,
        }

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return False

    # def _resource_types(self, dataset_type):
    #     '''
    #     returns a list of supported resource based on the dataset_type
    #     '''
    #     # TODO

    #     return self.package_types()


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

    # def read_template(self):
    #     return 'package/read.html'

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
        '''
        The create_package_schema() function is used whenever
        a new dataset is created, we'll want update the default 
        schema and insert our custom field here. 
        We will fetch the default schema defined in default_create_package_schema() 
        by running create_package_schema()'s super function and update it.
        '''

        # schema = super(toolkit.DefaultDatasetForm, self).create_package_schema()
        schema = default_create_package_schema()

        return _modify_package_schema(schema)

    def update_package_schema(self):
        '''
        The CKAN schema is a dictionary where the key is the name of the field
        and the value is a list of validators and converters.
        Here we have a validator to tell CKAN to not raise a validation error if
        the value is missing and a converter to convert the value to and save
        as an extra. 
        We will want to change the update_package_schema() function with the
        same update code.
        '''
        schema = default_update_package_schema()

        return _modify_package_schema(schema)

    def show_package_schema(self):
        '''
        The show_package_schema() is used when the package_show() action is 
        called, we want the default_show_package_schema to be updated to 
        include our custom field. 
        This time, instead of converting to an extras field, we want our 
        field to be converted from an extras field.
        So we want to use the convert_from_extras() converter.
        '''
        schema = default_show_package_schema()

        # TODO why?!?!? this has been fixed in scheming 
        # but core now is broken... :(
        for field in schema['resources'].keys():
            if isodate in schema['resources'][field]:
                schema['resources'][field].remove(isodate)

        # schema.get('__before').append(_v.resource_serializer)
        # schema.get('__before', []).append(_v.serializer)
        return schema
        
def _modify_package_schema(schema):
    # insert in front
    schema.get('__before').insert(0, _v.resource_extractor)
    schema.get('__before').insert(0, _v.extractor)
    # the following will be the first...
    schema.get('__before').insert(0, _v.schema_check)
    return schema
