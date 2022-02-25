import ckanext.jsonschema.constants as _c

PACKAGE_OPERATIONS = ['input', 'supported', 'output', 'clone']

def get_input_configuration():
    return _c.JSON_CATALOG[_c.JSON_CONFIG_KEY]

def get_configuration_template():

    configuration_template = {}
    for op in PACKAGE_OPERATIONS:
        configuration_template[op] = {}

    return configuration_template

def get_configuration():
    return _c.JSONSCHEMA_CONFIG

def set_configuration(configuration):
    _c.JSONSCHEMA_CONFIG = configuration


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

                jsonschema_type_config['plugin_name'] = plugin_name

        # insert the resource into every operation of the type
        if 'resources' in jsonschema_type:     
            resources = jsonschema_type['resources']
            _configure_resources(resources, jsonschema_type_name, configuration, plugin_name)


def _check_double_declaration(jsonschema_type_name, jsonschema_type_config, plugin_name, operation):
    '''
    Checks if the current jsonschema_type was already declared with the current operations
    Because only one plugin may support an operation for a jsonschema_type, this method raise an exception if the check fails
    '''
    if 'plugin_name' in jsonschema_type_config:
        message = 'Both plugins {} and {} declare the type "{}" for "{}" operation; this is not supported'
        message = message.format(jsonschema_type_config['plugin_name'], plugin_name, jsonschema_type_name, operation)
        raise Exception(message)



def _configure_resources(resources, jsonschema_type_name, configuration, plugin_name):

    for resource_type, resource in resources.items():
        for operation in PACKAGE_OPERATIONS:
            if operation in resource and resource[operation]:

                if 'resources' not in configuration[operation][jsonschema_type_name]:
                    configuration[operation][jsonschema_type_name]['resources'] = {}

                configuration[operation][jsonschema_type_name]['resources'][resource_type] = {'plugin_name': plugin_name}


# GETTERS

def get_input_types():

    configuration = get_configuration()
    input_types = configuration['input'].keys()

    return input_types

def get_supported_types():

    configuration = get_configuration()
    supported_types = configuration['supported'].keys()

    return supported_types

def get_resource_types(pacakge_type=None):
    '''
    If dataset_type is None: returns a map {pacakge_type1: [resource_type1, resource_type2...], package_type2: ...}
    If dataset_type is set, returns the list of resources supported for that dataset_type
    '''


    configuration = get_configuration()
    resource_types = {}
    
    for package_type_name in configuration['supported']:
        package_type_configuration = configuration['supported'][package_type_name]
        if 'resources' in package_type_configuration:
            resource_types[package_type_name] = package_type_configuration['resources'].keys()
            
    if pacakge_type:
        return resource_types[pacakge_type]
    else:
        return resource_types

def get_output_types():

    configuration = get_configuration()
    output_types = configuration['output'].keys()

    return output_types
