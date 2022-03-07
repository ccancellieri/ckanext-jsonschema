import ckanext.jsonschema.interfaces as _i
import ckanext.jsonschema.utils as _u
import ckanext.jsonschema.constants as _c
from ckan.plugins import PluginImplementations

JSONSCHEMA_IVIEW_PLUGINS = PluginImplementations(_i.IJsonschemaView)

VIEWS_KEY = 'views'
CONFIG_KEY = 'config'
INFO_KEY = 'info'

def get_views(config):
    return config.get(VIEWS_KEY)

def get_config(config):
    return config.get(CONFIG_KEY)

def get_info(config):
    return config.get(INFO_KEY)

def is_jsonschema_view(view_type):

    for plugin in JSONSCHEMA_IVIEW_PLUGINS:
        info = plugin.info()

        if info['name'] == view_type:
            return True

    return False
        
def _get_view(config, format, jsonschema_type=None):
    
    config_views = config.get(VIEWS_KEY)

    for view in config_views:

        if format.lower() == view.get('format'):
            if not jsonschema_type and 'jsonschema_type' not in view:
                return view
            
            if jsonschema_type and jsonschema_type == view.get('jsonschema_type'):
                return view
        
    raise Exception('Misconfigured view for format: {} and jsonschema_type: {}'.format(format, jsonschema_type))

def get_schema(config, format, jsonschema_type=None):
    catalog_key = get_schema_type(config, format, jsonschema_type)
    schema = _c.JSON_CATALOG[_c.JSON_SCHEMA_KEY].get(catalog_key) 
    return schema

def get_schema_type(config, format, jsonschema_type=None):
    view = _get_view(config, format, jsonschema_type)
    return _u._get_key(view.get('schema'))

def get_template(config, format, jsonschema_type=None):
    view = _get_view(config, format, jsonschema_type)

    view_template = view.get('template')
    template = {}
    
    if view_template:
        catalog_key = _u._get_key(view.get('template'))
        template = _c.JSON_CATALOG[_c.JSON_TEMPLATE_KEY].get(catalog_key) 
        
    return template
