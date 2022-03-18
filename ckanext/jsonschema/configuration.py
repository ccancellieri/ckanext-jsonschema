import ckanext.jsonschema.constants as _c
from ckanext.jsonschema.interfaces import JSONSCHEMA_IBINDER_PLUGINS

from ckan.plugins.core import PluginNotFoundException
import logging
log = logging.getLogger(__name__)

# INPUT_KEY = 'input'
# SUPPORTED_KEY = 'supported'
# OUTPUT_KEY = 'output'
# CLONE_KEY = 'clone'
PLUGIN_KEY = 'plugin'
# PACKAGE_OPERATIONS = [INPUT_KEY, SUPPORTED_KEY, OUTPUT_KEY, CLONE_KEY]

# INPUT_TYPES = []
# SUPPORTED_TYPES = []
# RESOURCE_TYPES = []
# OUTPUT_TYPES = []

PACKAGE_REGISTRY_KEY = 'package-registry'
RESOURCE_REGISTRY_KEY = 'resource-registry'
############# SETUP #############



# def get_input_configuration():
#     '''
#     Returns the configuration file provided in ckanext/config
#     '''
#     return _c.JSON_CATALOG[_c.JSON_CONFIG_KEY]

# def get_configuration_template():
#     '''
#     Returns a template configuration to be filled with the setup
#     '''

#     configuration_template = {}
#     for op in PACKAGE_OPERATIONS:
#         configuration_template[op] = {}

#     return configuration_template

# def get_configuration():
#     '''
#     Returns the internal representation of the configuration
#     '''
#     return _c.JSONSCHEMA_CONFIG

# def set_configuration(configuration):
#     _c.JSONSCHEMA_CONFIG = configuration


# def get_plugin(operation, dataset_type, resource_type=None):
#     '''
#     Gets the plugin instance from the configuration that handles the specified dataset_type or resource_type under the dataset_type
#     '''

#     configuration = get_configuration()

#     try:
#         if resource_type:
#             plugin = configuration.get(operation).get(dataset_type).get('resources').get(resource_type).get(PLUGIN_KEY)
#         else:
#             plugin = configuration.get(operation).get(dataset_type).get(PLUGIN_KEY)
    
#         if not plugin:
#             raise Exception()
        
#         return plugin

#     except:
#         raise PluginNotFoundException('No plugin configured for operation: {}, dataset_type: {}, resource_type: {}'.format(operation, dataset_type, resource_type))


# def setup():
#     '''
#     This module reads from the JSON_CATALOG and performs initialization steps from the jsonschema plugin configuration
#     1) Checks that the configurations are correct
#     2) Creates a data structure used in the plugin to retrieve information about the configuration

#     The configuration structure is the following:

#     "clone": {
#         "iso": {
#             "plugin_name": "jsonschema_iso",
#             "resources": {
#                 "online-resource": {
#                     "plugin_name": "jsonschema_iso"
#                 }
#             }
#         },
#         "iso19139": {
#             ...
#         }
#     },
#     "create": {
#         ...
#     }
#     ...
    
#     '''

#     _validate_configuration_files()

#     configuration = get_configuration_template()
#     create_configuration(configuration)
#     set_configuration(configuration)

#     _validate_schemas()

#     log.info('Created jsonschema configuration')

# def create_configuration(configuration):
#     input_configuration = get_input_configuration()

#     for plugin_name, plugin_configuration in input_configuration.items():

#         jsonschema_types = plugin_configuration['jsonschema_types']
#         _configure_jsonschema_types(jsonschema_types, configuration, plugin_name)

# def _configure_jsonschema_types(jsonschema_types, configuration, plugin_name):

#     for jsonschema_type_name, jsonschema_type in jsonschema_types.items():

#         # insert the jsonschema_type into every operation that it supports            
#         for operation in PACKAGE_OPERATIONS:

#             if operation in jsonschema_type and jsonschema_type[operation]:

#                 if jsonschema_type_name not in configuration[operation]:
#                     configuration[operation][jsonschema_type_name] = {} #init the object for this type
#                 jsonschema_type_config = configuration[operation][jsonschema_type_name] 

#                 _check_double_declaration(jsonschema_type_name, jsonschema_type_config, plugin_name, operation)

#                 jsonschema_type_config[PLUGIN_KEY] = _lookup_jsonschema_plugin_from_name(plugin_name)

#         # insert the resource into every operation of the type
#         if 'resources' in jsonschema_type:     
#             resources = jsonschema_type['resources']
#             _configure_resources(resources, jsonschema_type_name, configuration, plugin_name)


# def _check_double_declaration(jsonschema_type_name, jsonschema_type_config, plugin_name, operation):
#     '''
#     Checks if the current jsonschema_type was already declared with the current operations
#     Because only one plugin may support an operation for a jsonschema_type, this method raise an exception if the check fails
#     '''
#     if PLUGIN_KEY in jsonschema_type_config:
#         message = 'Both plugins {} and {} declare the type "{}" for "{}" operation; this is not supported'
#         message = message.format(jsonschema_type_config[PLUGIN_KEY], plugin_name, jsonschema_type_name, operation)
#         raise Exception(message)



# def _configure_resources(resources, jsonschema_type_name, configuration, plugin_name):

#     for resource_type, resource in resources.items():
#         for operation in PACKAGE_OPERATIONS:
#             if operation in resource and resource[operation]:

#                 if 'resources' not in configuration[operation][jsonschema_type_name]:
#                     configuration[operation][jsonschema_type_name]['resources'] = {}

#                 configuration[operation][jsonschema_type_name]['resources'][resource_type] = {PLUGIN_KEY: _lookup_jsonschema_plugin_from_name(plugin_name)}

# ############# END SETUP #############




############# VALIDATIONS #############

# def validate_configuration():
#     '''
#     Checks that the configuration is correct
#     1) There should be a schema for every configured dataset type
#     '''
#     # validate plugins with IBinder


# def _validate_schemas():

#     schemas = _c.JSON_CATALOG[_c.JSON_SCHEMA_KEY]
#     supported_types = get_supported_types()

#     for type in supported_types:
#         if type not in schemas:
#             raise Exception('The jsonschema type "{}" was configured but its schema was not found'.format(type))

# def _validate_configuration_files():
#     '''Checks that every jsonschema_plugin has its own configuration file'''

#     for plugin in JSONSCHEMA_IBINDER_PLUGINS:
#         configuration_files = get_input_configuration().keys()
#         if plugin.name not in configuration_files:
#             raise PluginNotFoundException('The plugin {} was installed but no configuration file was found'.format(plugin.name)) 


############# END VALIDATIONS #############


def get_package_registry():
    return _c.JSON_CATALOG[_c.JSON_REGISTRY_KEY].get(PACKAGE_REGISTRY_KEY)

def get_resource_registry():
    return _c.JSON_CATALOG[_c.JSON_REGISTRY_KEY].get(RESOURCE_REGISTRY_KEY)

def get_plugin(dataset_type, resource_type=None):
    '''
    Gets the plugin instance from the configuration that handles the specified dataset_type or resource_type under the dataset_type
    '''
    if resource_type:
        registry = get_resource_registry()
        plugin_name = registry.get(resource_type).get('plugin_name')

        # this raises AttributeError: 'NoneType' object has no attribute 'get' if not configured
        # must raise a speaking message

    else:
        registry = get_package_registry()
        plugin_name = registry.get(dataset_type).get('plugin_name')

        # this raises AttributeError: 'NoneType' object has no attribute 'get' if not configured
        # must raise a speaking message

    
    plugin = _lookup_jsonschema_plugin_from_name(plugin_name)

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
    return get_configuration().get(OUTPUT_KEY).keys()

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


def _lookup_jsonschema_plugin_from_name(plugin_name):

    for plugin in JSONSCHEMA_IBINDER_PLUGINS:
        if plugin.name == plugin_name:
            return plugin
            
    raise PluginNotFoundException('Found a configuration file for plugin {} which is not installed'.format(plugin_name))    