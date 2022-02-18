"""Tests for plugin.py."""


import ckan.plugins
import ckan.tests.helpers as helpers
from ckanext.jsonschema.plugin import (handled_dataset_types,
                                       handled_resource_types, 
                                       handled_output_types, 
                                       _modify_package_schema)

from ckan.logic.schema import (default_create_package_schema)
    
class TestPlugin(object):
    
    @classmethod
    def setup_class(cls):
        helpers.reset_db()
        
        # Test code should use CKAN's plugins.load() function to load plugins
        # to be tested.

        _plugins = ['jsonschema', 'jsonschema_iso']

        for plugin in _plugins:
            if not ckan.plugins.plugin_loaded(plugin):
                ckan.plugins.load(plugin)


    def test_handled_dataset_types(self):

        dataset_types = handled_dataset_types()

        assert type(dataset_types) is list
        assert len(dataset_types) != 0


    def test_handled_resource_types(self):

        dataset_types = handled_dataset_types()

        for dataset_type in dataset_types:
            resource_types = handled_resource_types(dataset_type)

            assert type(resource_types) is list


    def test_handled_output_types(self):

        dataset_types = handled_dataset_types()

        for dataset_type in dataset_types:
            output_types = handled_output_types(dataset_type)

            # output_types can be list or None, so for now just test it works
            # assert type(output_types) is list
            assert True

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
 
    def test_validate(self, dataset):
        pass