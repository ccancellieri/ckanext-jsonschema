"""Tests for plugin.py."""


import ckan.plugins
import ckan.tests.helpers as helpers
from ckan.logic.schema import default_create_package_schema
from ckanext.jsonschema.plugin import _modify_package_schema


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
