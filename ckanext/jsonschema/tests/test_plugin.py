"""Tests for plugin.py."""


import ckan.plugins
import ckan.tests.helpers as helpers
import ckanext.jsonschema.configuration as configuration
from ckan.logic.schema import default_create_package_schema
from ckan.plugins.core import PluginNotFoundException
from ckanext.jsonschema.plugin import _modify_package_schema


class TestPlugin(object):
    
    @classmethod
    def setup_class(cls):
        helpers.reset_db()
        
        # Test code should use CKAN's plugins.load() function to load plugins
        # to be tested.

        _plugins = ['jsonschema']

        for plugin in _plugins:
            if not ckan.plugins.plugin_loaded(plugin):
                ckan.plugins.load(plugin)


    def test_modify_package_schema(self):

        from six import PY3

        schema = default_create_package_schema()
        schema = _modify_package_schema(schema)

        for modified_schema_function in ['schema_check', 'before_extractor', 'extractor', 'resource_extractor']:

            if PY3:
                funcs = [fun for fun in schema['__before'] if fun.__name__ == modified_schema_function]
            else:
                funcs = [fun for fun in schema['__before'] if fun.func_name == modified_schema_function]
            
            found = len(funcs) > 0
            assert found


    def test_configuration(self):

        from six import PY3

        # When getting .keys() from a dict in Python3, the returned object is of type dict_keys instead of list
        if PY3:
            list_type = type({}.keys())
        else:
            list_type = list

        input_configuration = configuration.get_input_configuration()
        assert isinstance(input_configuration, dict)

        configuration.setup()

        try:
            configuration._get_jsonschema_plugin_from_name("random_plugin_name")
            assert False('No error was raised when requesting to configuration a non existing plugin')
        except PluginNotFoundException:
            assert True

        input_types = configuration.get_input_types()
        assert isinstance(input_types, list_type)
        
        output_types = configuration.get_output_types()
        assert isinstance(output_types, list_type)

        supported_types = configuration.get_supported_types()
        assert isinstance(supported_types, list_type)

        if len(supported_types) > 0:
            resource_types = configuration.get_resource_types(supported_types[0])
            assert isinstance(resource_types, list_type)

