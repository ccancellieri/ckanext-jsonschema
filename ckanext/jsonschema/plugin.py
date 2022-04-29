import json

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.jsonschema.blueprints as _b
import ckanext.jsonschema.configuration as configuration
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.logic.action.action as action
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.validators as _v
import ckanext.jsonschema.view_tools as _vt
from ckan.logic.schema import (default_create_package_schema,
                               default_update_package_schema,
                               default_show_package_schema)

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


import logging

from ckan.logic.schema import default_show_package_schema

    # let's grab the default schema in our plugin

log = logging.getLogger(__name__)


class JsonschemaPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions)

    #IActions
    def get_actions(self):
        from ckanext.jsonschema.logic.action.get import reload
        from ckanext.jsonschema.logic.actions import (clone_metadata, importer,
                                                      validate_metadata, view_show, spatial_search)

        actions = {
            'jsonschema_importer': importer,
            'jsonschema_reload': reload,
            'jsonschema_validate': validate_metadata,
            'jsonschema_clone': clone_metadata,
            'jsonschema_view_show': view_show,
            'jsonschema_spatial_search': spatial_search,

            # CHAINED CKAN ACTIONS
            'resource_create': action.resource_create,
            'resource_update': action.resource_update,
            'resource_view_create': action.resource_view_create,
            'resource_view_update': action.resource_view_update,
            'resource_view_delete': action.resource_view_delete
        }
        return actions

    # IBlueprint
    
    def get_blueprint(self):
        return _b.jsonschema
    
    # ITemplateHelpers

    def get_helpers(self):
        return {
            ######## DEPRECATED ########
            # These are used only on forms to send key - value
            'jsonschema_get_body_key': lambda : _c.SCHEMA_BODY_KEY,
            'jsonschema_get_type_key': lambda : _c.SCHEMA_TYPE_KEY,
            'jsonschema_get_opt_key': lambda : _c.SCHEMA_OPT_KEY,
            ############################

            'jsonschema_as_json': lambda payload : _t.as_json(payload),

            'jsonschema_get_package_body': lambda d : _t.as_dict(_t.safe_helper(_t.get_package_body, d)),
            'jsonschema_get_package_type': _t.get_package_type,
            'jsonschema_get_package_opt': lambda d : _t.as_dict(_t.safe_helper(_t.get_package_opt, d, _c.SCHEMA_OPT)),

            #'jsonschema_get_resource': lambda r = None : _t.get(r),
            'jsonschema_get_resource_body': lambda r, template = {} : _t.as_dict(_t.safe_helper(_t.get_resource_body, r, template)),
            'jsonschema_get_resource_type': lambda r, default_type = None : _t.safe_helper(_t.get_resource_type, r, default_type),
            'jsonschema_get_resource_opt': lambda r : _t.as_dict(_t.safe_helper(_t.get_resource_opt, r, _c.SCHEMA_OPT)),

            # view helpers
            'jsonschema_get_view_body': lambda r, template = {} : _t.as_dict(_t.safe_helper(_vt.get_view_body, r, template)),
            'jsonschema_get_view_type': lambda r, default_type = None : _t.safe_helper(_vt.get_view_type, r, default_type),
            'jsonschema_get_view_opt': lambda r : _t.as_dict(_t.safe_helper(_vt.get_view_opt, r, _c.SCHEMA_OPT)),
            'jsonschema_url_quote': _t.url_quote,
            'jsonschema_is_jsonschema_view': _vt.is_jsonschema_view,
            #'jsonschema_get_view_types': _vt.get_view_types,
            'jsonschema_get_configured_jsonschema_types_for_plugin_view': _vt.get_configured_jsonschema_types_for_plugin_view,
            'jsonschema_get_view_info': _vt.get_view_info,
            'jsonschema_get_rendered_resource_view': _vt.rendered_resource_view,

            # DEFAULTS
            'jsonschema_get_schema': lambda x : json.dumps(_t.get_schema_of(x)),
            'jsonschema_get_template': lambda x : json.dumps(_t.get_template_of(x)),
            'jsonschema_get_opt': lambda : _c.SCHEMA_OPT,
            'jsonschema_get_default_license': lambda : _c.DEFAULT_LICENSE,

            'jsonschema_handled_resource_types': configuration.get_supported_resource_types,
            'jsonschema_handled_dataset_types': configuration.get_supported_types,
            'jsonschema_handled_input_types': configuration.get_input_types,
            'jsonschema_handled_output_types': configuration.get_output_types,
            
            #'jsonschema_get_resource_label': configuration.get_resource_label
            #jsonschema_get_runtime_opt': lambda x : json.dumps(_t.get_opt_of(x)),
            'jsonschema_get_label_from_registry': _t.get_label_from_registry,

            # FORM CONFIGURATION
            'jsonschema_is_supported_ckan_field': _t.is_supported_ckan_field,
            'jsonschema_is_supported_jsonschema_field': _t.is_supported_jsonschema_field,

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
        

    def before_index(self, pkg_dict):
    # IMPORTANT: Check already existing views on not available plugin
    # ckan/lib/datapreview/resource_view_list filters out views for which the plugin is no more available

        # TODO use IBinder to define extension points by plugin
        package = json.loads(pkg_dict['data_dict'])
        package_id = package.get('id')
        # site_id = pkg_dict.get('site_id')

        package_jsonschema_type = _t.get_package_type(package)

        # if get_skip_index_from_registry(package_jsonschema_type):
            #return pkg_dict
        package_plugin = configuration.get_plugin(package_jsonschema_type)

        try:
            pkg_dict = package_plugin.before_index_package(pkg_dict)
        except Exception as e:
            log.error(str(e))
        
        
        resources = package.get('resources')

        res_ids = []
        res_descriptions = []
        res_jsonschema_types = []
        res_jsonschemas = []
        
        views = []
        for resource in resources:
            
            # TODO filter only active resources/views

            # TODO use IBinder to define extension points by plugin (resource type)
            # TODO
            #  use iso plugin to implement https://github.com/ckan/ckanext-spatial/blob/4ac25f19aa4eb9c798451f5eeb3084f907ccc003/ckanext/spatial/plugin.py#L187
            #  check also iso19139/tools.py

            
            resource_id = resource.get('id')
            res_ids.append(resource_id)
            res_descriptions.append(resource.get('description'))
            
            resource_jsonschema_type = _t.get_resource_type(resource)
            # if get_skip_index_from_registry(resource_jsonschema_type):
                # continue
        
            # do not index jsonschema fields if regular type
            if resource_jsonschema_type:
                res_jsonschema_types.append(resource_jsonschema_type)
                res_jsonschemas.append({
                    'resource_id' : resource_id,
                    _c.SCHEMA_TYPE_KEY : resource_jsonschema_type,
                    _c.SCHEMA_BODY_KEY : _t.get_resource_body(resource) or None,
                    _c.SCHEMA_OPT_KEY : _t.get_resource_opt(resource) or None
                })

            resource_views = toolkit.get_action('resource_view_list')({}, {'id': resource_id})
            for view in resource_views:

                view_jsonschema_type = _vt.get_view_type(view)
                # TODO
                # if get_skip_index_from_registry(view_jsonschema_type):
                    # continue

                # do not index non-jsonschema views
                if not view_jsonschema_type:
                    continue

                view_id = view.get('id')
                view_type = view.get('view_type')
                
                view_plugin = _vt.get_jsonschema_view_plugin(view_type)

                # TODO: before_index_view
                # TODO use IBinder to define extension points by plugin (resource view type)

                view_jsonschema_body = _vt.get_view_body(view)
                view_jsonschema_body_resolved = view_jsonschema_body

                if view_plugin:
                    try:
                        view_jsonschema_body_resolved = view_plugin.resolve(_t.as_dict(view_jsonschema_body), view)
                    except Exception as e:
                        log.error('Error while resolving view.')
                        log.error('Package id:{}, resource id:{}, view id: {}'.format(package_id, resource_id, view_id))
                        log.error(str(e))
                else:
                    log.warn('No plugin found for view_type: {}'.format(view_type))
            
                views.append({
                        'view_id': view_id,
                        'view_type': view_type,
                        '{}'.format(_c.SCHEMA_TYPE_KEY): view_jsonschema_type,
                        '{}'.format(_c.SCHEMA_BODY_KEY): view_jsonschema_body or None,
                        '{}_resolved'.format(_c.SCHEMA_BODY_KEY): view_jsonschema_body_resolved or None,
                        '{}'.format(_c.SCHEMA_OPT_KEY): _vt.get_view_opt(view) or None
                    })

        pkg_dict.update({
            'res_ids': res_ids,
            'res_descriptions': res_descriptions,
            'res_jsonschemas': res_jsonschemas,
            'res_jsonschema_types': res_jsonschema_types,
            'view_ids': [view.get('view_id') for view in views],
            'view_types': [view.get('view_type') for view in views],
            'view_jsonschema_types': [view.get(_c.SCHEMA_TYPE_KEY) for view in views],
            'view_jsonschemas': [json.dumps(view) for view in views]
        })

        log.info('Indexed package: {}'.format(pkg_dict.get('id')))
        return pkg_dict
        
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

        #import ckanext.jsonschema.indexer as indexer
        #indexer.init_core('jsonschema_core')
        
    # IConfigurable
    def configure(self, config):
        _t.reload()

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

        package_types = []

        for package_type in configuration.get_supported_types():
            if package_type not in package_types:
                package_types.append(package_type)
        
        for package_type in configuration.get_input_types():
            if package_type not in package_types:
                package_types.append(package_type)
        
        return package_types

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
    #     return 'package/snippets/package_form.html'

    # # TODO: https://github.com/ckan/ckan/issues/6518 (related but available on 2.9.x)
    def read_template(self):
        #TODO
        # If you want to render a specific view for a specific jsonschema type, use this method to return the template
        # package_type = _t.get_package_type(toolkit.c.pkg_dict)
        return 'source/read.html'

    # def edit_template(self):
    #     return 'package/snippets/package_form.html'

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
        schema = default_create_package_schema()
        return _v.modify_package_schema(schema)

    def update_package_schema(self):
        schema = default_update_package_schema()
        return _v.modify_package_schema(schema)

    def show_package_schema(self):
        schema = default_show_package_schema()
        return _v.show_package_schema(schema)
