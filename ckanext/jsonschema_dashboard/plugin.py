from os import path

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.interfaces as _i
import ckanext.jsonschema_dashboard.constants as _dc
import ckanext.jsonschema_dashboard.tools as _dt
import ckanext.jsonschema_dashboard.blueprints as _b
import ckanext.jsonschema.validators as _v
import ckanext.jsonschema.utils as _u

get_validator = toolkit.get_validator
not_empty = get_validator('not_empty')
ignore_empty = get_validator('ignore_empty')

PLUGIN_NAME = 'jsonschema_dashboard'

class JsonschemaDashboard(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IResourceView)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(_i.IJsonschemaView)


    # ITemplateHelpers
    def get_helpers(self):
        return {
            'jsonschema_is_jsonschema_view': _dt.is_jsonschema_view,
        }

    # IConfigurer 
    def update_config(self, config_):

        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')

        jsonschema_fantastic = path.join(_c.PATH_ROOT,'jsonschema', 'fanstatic')

        toolkit.add_resource(jsonschema_fantastic, 'jsonschema_editor')

        self.config = _u._json_load(_dc.PATH_CONFIG, _dc.CONFIG_FILENAME)


    # IResourceView
    
    def can_view(self, data_dict):
    
        resource = data_dict.get('resource',None)
    
        #TODO Try except?
        # view_configuration.can_view(resource)

    # IBlueprint
    def get_blueprint(self):
        return _b.jsonschema


    def info(self):

        # DO WE NEED THIS?
        def default_config(plugin_name):
            return _dt.get_config(self.config)

        info = {
            u'iframed': False,
            #u'filterable': False,
            u'name': self.name,

            # TODO MOVE IN JSONSCHEMA PLUGIN
            u'schema': {
                _c.SCHEMA_TYPE_KEY: [not_empty], # import
                _c.SCHEMA_BODY_KEY: [not_empty, _v.view_schema_check],
                _c.SCHEMA_OPT_KEY: [default_config] 
            },
            u'requires_datastore': False
        }

        plugin_info = _dt.get_info(self.config)

        info.update(plugin_info)

        return info

    def setup_template_variables(self, context, data_dict):
    #TODO Do we need this? Could conflict with package's setup_template_variables

        resource = data_dict.get('resource')
        format = resource.get('format')
        resource_jsonschema_type = _t.get_resource_type(resource)

        resource_view = data_dict.get('resource_view', {})

        data_dict.update({
            'config_view': {
                #'config': _dt.get_config(self.config),
                _c.SCHEMA_TYPE_KEY: _dt.get_schema_type(self.config, format, resource_jsonschema_type),
                _c.SCHEMA_BODY_KEY: resource_view.get(_c.SCHEMA_BODY_KEY, _dt.get_template(self.config, format, resource_jsonschema_type)),
                _c.SCHEMA_OPT_KEY: resource_view.get(_c.SCHEMA_OPT_KEY, _dt.get_config(self.config))
            },
            _c.JSON_SCHEMA_KEY: _dt.get_schema(self.config, format, resource_jsonschema_type),
        })

        return data_dict

    def view_template(self, context, data_dict):
        # data_dict will tell the jsonschema_type -> plugin
        #view_configuration.get_plugin(...)
        #plugin.view_template(...)

        return 'view_template.html'

    def form_template(self, context, data_dict):
        
        #default form template
        #use jsonschema default template and get tools, model... from terria
        #use plugin's or default
        return 'view_form.html'