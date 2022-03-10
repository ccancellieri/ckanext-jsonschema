import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.interfaces as _i
from ckan.plugins import PluginImplementations
from ckan.plugins.core import PluginNotFoundException

JSONSCHEMA_IVIEW_PLUGINS = PluginImplementations(_i.IJsonschemaView)
OPTIONS_KEY = "options"
INFO_KEY = "info"


def get_input_configuration():
    '''
    Returns the configuration file provided in ckanext/view_config
    '''
    return _c.JSON_CATALOG[_c.JSON_VIEW_CONFIG_KEY]

def setup():

    # TODO check that every configured plugin is there
    # validate_configuration_files()
    pass

def can_view(resource):
    import ckanext.jsonschema.tools as _t

    jsonschema_type = _t.get_resource_type(resource)
    format = resource.get('format')

    input_configuration = get_input_configuration()

    for keys, item in input_configuration.items():
        for plugin_name, plugin_config in item.items():

            if format == plugin_config.get('format'):
                
                # TODO check that schema exists
                if not jsonschema_type:
                    return True
                
                elif jsonschema_type:
                    if item.get(_c.SCHEMA_TYPE_KEY) == jsonschema_type:
                        return True
    
    return False


def get_schema(plugin_name, format, jsonschema_type=None, ):
    pass

def get_template(plugin_name, format, jsonschema_type=None):
    pass    

def get_options(plugin_name):

    input_configuration = get_input_configuration()
    
    return input_configuration.get(OPTIONS_KEY).get(plugin_name)
    
def get_info(plugin_name):

    options = get_options(plugin_name)

    return options.get(INFO_KEY)


def _lookup_jsonschema_plugin_from_name(plugin_name):

    for plugin in JSONSCHEMA_IVIEW_PLUGINS:
        if plugin.name == plugin_name:
            return plugin
            
    raise PluginNotFoundException('Found a configuration file for plugin {} which is not installed'.format(plugin_name))
