import ckanext.jsonschema.constants as _c
from ckanext.jsonschema.interfaces import JSONSCHEMA_IBINDER_PLUGINS

from ckan.plugins.core import PluginNotFoundException
import logging
log = logging.getLogger(__name__)

PLUGIN_KEY = 'plugin'


def get_registry():
    return _c.JSON_CATALOG[_c.JSON_REGISTRY_KEY]

def get_plugin(package_type, resource_type=None):
    '''
    Gets the plugin instance from the configuration that handles the specified package_type or resource_type under the package_type
    At the moment the relationship between package_type and resource_type is not taken into account, but both the parameter are still requested so that they could
    be used in the future
    '''

    try:
        
        plugin_name = ""
        registry = get_registry()

        if resource_type:
            plugin_name = registry.get(resource_type).get('plugin_name')

            # this raises AttributeError: 'NoneType' object has no attribute 'get' if not configured
            # must raise a speaking message

        else:
            plugin_name = registry.get(package_type).get('plugin_name')

            # this raises AttributeError: 'NoneType' object has no attribute 'get' if not configured
            # must raise a speaking message

        plugin = _lookup_jsonschema_plugin_from_name(plugin_name)

    except (TypeError, AttributeError):
        raise PluginNotFoundException('The requested plugin: {} was not found'.format(plugin_name))    

    return plugin

############# GETTERS ############# 
def get_input_types():

    input_types = []
    for plugin in JSONSCHEMA_IBINDER_PLUGINS:
        for input_type in plugin.get_input_types():
            if input_type not in input_types:
                input_types.append(input_type)

    return input_types

def get_supported_types():
    
    supported_types = []
    for plugin in JSONSCHEMA_IBINDER_PLUGINS:
        for supported_type in plugin.get_supported_types():
            if supported_type not in supported_types:
                supported_types.append(supported_type)

    return supported_types

def get_output_types():
    # Currently this isn't used because we never need a list of outputtable types

    output_types = []
    for plugin in JSONSCHEMA_IBINDER_PLUGINS:
        for output_type in plugin.get_output_types():
            if output_type not in output_types:
                output_types.append(output_type)

    return output_types

def get_supported_resource_types(package_type):
    '''
    This resources every resource configured by the plugins
    package_type could be use to filter resources available for specific package_types
    '''

    supported_resource_types = []
    for plugin in JSONSCHEMA_IBINDER_PLUGINS:
        for supported_resource_type in plugin.get_supported_resource_types():
            if supported_resource_type not in supported_resource_types:
                supported_resource_types.append(supported_resource_type)

    return supported_resource_types
################################### 


def _lookup_jsonschema_plugin_from_name(plugin_name):

    for plugin in JSONSCHEMA_IBINDER_PLUGINS:
        if plugin.name == plugin_name:
            return plugin
            
    raise PluginNotFoundException('The requested plugin: {} was not found'.format(plugin_name))    