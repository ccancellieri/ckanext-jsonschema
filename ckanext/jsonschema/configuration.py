import ckanext.jsonschema.constants as _c
from ckan.plugins.core import PluginNotFoundException

INPUT_KEY = 'input'
SUPPORTED_KEY = 'supported'
OUTPUT_KEY = 'output'
CLONE_KEY = 'clone'
PLUGIN_KEY = 'plugin'
PACKAGE_OPERATIONS = [INPUT_KEY, SUPPORTED_KEY, OUTPUT_KEY, CLONE_KEY]

# TODO move me and relatives to plugin.pu
import ckanext.jsonschema.interfaces as _i
from ckan.plugins import PluginImplementations
JSONSCHEMA_PLUGINS = PluginImplementations(_i.IBinder)

INPUT_TYPES = []
SUPPORTED_TYPES = []
RESOURCE_TYPES = []
OUTPUT_TYPES = []

############# SETUP #############
def get_input_configuration():
    '''
    Returns the configuration file provided in ckanext/config
    '''
    return _c.JSON_CATALOG[_c.JSON_CONFIG_KEY]

def get_configuration_template():
    '''
    Returns a template configuration to be filled with the setup
    '''

    configuration_template = {}
    for op in PACKAGE_OPERATIONS:
        configuration_template[op] = {}

    return configuration_template

def get_configuration():
    '''
    Returns the internal representation of the configuration
    '''
    return _c.JSONSCHEMA_CONFIG

def set_configuration(configuration):
    _c.JSONSCHEMA_CONFIG = configuration


def get_plugin(operation, dataset_type, resource_type=None):
    '''
    Gets the plugin instance from the configuration that handles the specified dataset_type or resource_type under the dataset_type
    '''

    configuration = get_configuration()

    try:
        if resource_type:
            plugin = configuration.get(operation).get(dataset_type).get('resources').get(resource_type).get(PLUGIN_KEY)
        else:
            plugin = configuration.get(operation).get(dataset_type).get(PLUGIN_KEY)
    
        return plugin

    except:
        raise PluginNotFoundException('No plugin configured for operation: {}, dataset_type: {}, resource_type: {}'.format(operation, dataset_type, resource_type))


def setup():
    '''
    This module reads from the JSON_CATALOG and performs initialization steps from the jsonschema plugin configuration
    1) Checks that the configurations are correct
    2) Creates a data structure used in the plugin to retrieve information about the configuration

    The configuration structure is the following:

    "clone": {
        "iso": {
            "plugin_name": "jsonschema_iso",
            "resources": {
                "online-resource": {
                    "plugin_name": "jsonschema_iso"
                }
            }
        },
        "iso19139": {
            ...
        }
    },
    "create": {
        ...
    }
    ...
    
    '''

    input_configuration = get_input_configuration()
    configuration = get_configuration_template()


    for plugin_name, plugin_configuration in input_configuration.items():

        jsonschema_types = plugin_configuration['jsonschema_types']
        _configure_jsonschema_types(jsonschema_types, configuration, plugin_name)
                        

    set_configuration(configuration)
    validate_configuration()


def validate_configuration():
    '''
    Checks that the configuration is correct
    1) There should be a schema for every configured dataset type
    '''
    _validate_schemas()
    # validate plugins with IBinder


def _validate_schemas():

    schemas = _c.JSON_CATALOG[_c.JSON_SCHEMA_KEY]
    supported_types = get_supported_types()

    for type in supported_types:
        if type not in schemas:
            raise Exception('The jsonschema type "{}" was configured but its schema was not found'.format(type))



def _configure_jsonschema_types(jsonschema_types, configuration, plugin_name):

    for jsonschema_type_name, jsonschema_type in jsonschema_types.items():

        # insert the jsonschema_type into every operation that it supports            
        for operation in PACKAGE_OPERATIONS:

            if operation in jsonschema_type and jsonschema_type[operation]:

                if jsonschema_type_name not in configuration[operation]:
                    configuration[operation][jsonschema_type_name] = {} #init the object for this type
                jsonschema_type_config = configuration[operation][jsonschema_type_name] 

                _check_double_declaration(jsonschema_type_name, jsonschema_type_config, plugin_name, operation)

                jsonschema_type_config[PLUGIN_KEY] = _get_jsonschema_plugin_from_name(plugin_name)

        # insert the resource into every operation of the type
        if 'resources' in jsonschema_type:     
            resources = jsonschema_type['resources']
            _configure_resources(resources, jsonschema_type_name, configuration, plugin_name)


def _check_double_declaration(jsonschema_type_name, jsonschema_type_config, plugin_name, operation):
    '''
    Checks if the current jsonschema_type was already declared with the current operations
    Because only one plugin may support an operation for a jsonschema_type, this method raise an exception if the check fails
    '''
    if PLUGIN_KEY in jsonschema_type_config:
        message = 'Both plugins {} and {} declare the type "{}" for "{}" operation; this is not supported'
        message = message.format(jsonschema_type_config[PLUGIN_KEY], plugin_name, jsonschema_type_name, operation)
        raise Exception(message)



def _configure_resources(resources, jsonschema_type_name, configuration, plugin_name):

    for resource_type, resource in resources.items():
        for operation in PACKAGE_OPERATIONS:
            if operation in resource and resource[operation]:

                if 'resources' not in configuration[operation][jsonschema_type_name]:
                    configuration[operation][jsonschema_type_name]['resources'] = {}

                configuration[operation][jsonschema_type_name]['resources'][resource_type] = {PLUGIN_KEY: _get_jsonschema_plugin_from_name(plugin_name)}

############# END SETUP #############


############# GETTERS ############# 
def get_input_types():
    return get_configuration().get(INPUT_KEY).keys()


def get_supported_types():
    return get_configuration().get(SUPPORTED_KEY).keys()

def get_output_types():
    return get_configuration().configuration[OUTPUT_KEY].keys()

def get_resource_types(dataset_type):
    '''
    If dataset_type is None: returns a map {pacakge_type1: [resource_type1, resource_type2...], package_type2: ...}
    If dataset_type is set, returns the list of resources supported for that dataset_type
    '''
    global RESOURCE_TYPES, RESOURCE_TYPES_ARRAY

    configuration = get_configuration()
    resource_types = {}

    for jsonschema_type_name in configuration[SUPPORTED_KEY]:
        package_type_configuration = configuration[SUPPORTED_KEY][jsonschema_type_name]

        if 'resources' in package_type_configuration:
            resource_types[jsonschema_type_name] = package_type_configuration['resources'].keys()
            
    
    return resource_types[dataset_type]
    

def _get_jsonschema_plugin_from_name(plugin_name):

    for plugin in JSONSCHEMA_PLUGINS:
        if plugin.name == plugin_name:
            return plugin
            
    raise PluginNotFoundException('Found a configuration file for plugin {} which is not installed'.format(plugin_name))