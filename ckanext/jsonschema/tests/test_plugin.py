'''Tests for plugin.py.'''


import ckan.plugins
import ckan.tests.helpers as helpers
import ckanext.jsonschema.configuration as configuration
from ckan.plugins.core import PluginNotFoundException



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



    #from ckan.logic.schema import default_create_package_schema
    #from ckanext.jsonschema.plugin import _modify_package_schema
    
    # def test_modify_package_schema(self):

    #     from six import PY3

    #     schema = default_create_package_schema()
    #     schema = _modify_package_schema(schema)

    #     for modified_schema_function in ['schema_check', 'before_extractor', 'extractor', 'resource_extractor']:

    #         if PY3:
    #             funcs = [fun for fun in schema['__before'] if fun.__name__ == modified_schema_function]
    #         else:
    #             funcs = [fun for fun in schema['__before'] if fun.func_name == modified_schema_function]
            
    #         found = len(funcs) > 0
    #         assert found


    def test_configuration(self):


        input_types = configuration.get_input_types()
        assert isinstance(input_types, list)
        
        # output_types = configuration.get_output_types()
        # assert isinstance(output_types, list)

        supported_types = configuration.get_supported_types()
        assert isinstance(supported_types, list)

        if len(supported_types) > 0:
            # we cast supported_types to list because in Python3 would be a dict_keys
            resource_types = configuration.get_supported_resource_types(list(supported_types)[0])
            assert isinstance(resource_types, list)
        
        
        try:
            configuration._lookup_jsonschema_plugin_from_name('random_plugin_name')
            assert False('No error was raised when requesting to configuration a non-existing plugin')
        except PluginNotFoundException:
            assert True

        try:
            configuration.get_plugin('random_dataset', 'random_resource_type')
            # Should raise PluginNotFoundException, so assert False if doesn't
            assert False  
        except PluginNotFoundException:
            assert True

        # TODO add test for working get_plugin also 

    def test_get_supported_resource_types_with_non_existing_package_type(self):
        # UPDATE 23/03: now get_supported_resource_types returns every supported resource
        # without taking into account the package type

    
        resource_types = configuration.get_supported_resource_types('non_existing_package_type')
    
        assert isinstance(resource_types, list)
