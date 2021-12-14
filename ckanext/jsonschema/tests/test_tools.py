"""Tests for tools.py."""

import json

import ckan.plugins
import ckan.tests.helpers as helpers
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t

from ckanext.jsonschema.tests.conftest import get_jsonschema_resource


def _test_getter(dataset_with_extras, func, is_json=True):
    """
    Template for testing some of the tools getter functions
    We call the getter (passed as the func parameter)
    If the function call works, we try to dump it (we don't care about the result of the dump, just that it is dumpable)
    If it works the test is okay; if something breaks then the test fails
    """

    # Test get functions on the dataset
    try:
        payload = func(dataset_with_extras.get('id'))

        if is_json:
            json.dumps(payload)

        assert payload is not None

    except Exception as e: 
        assert False(str(e))

    # Test get functions on the resource
    try:
        resource = get_jsonschema_resource(dataset_with_extras)   
        payload = func(dataset_with_extras.get('id'), resource.get('id')) 
        
        if is_json:
            json.dumps(payload)

        assert payload is not None

    except Exception as e: 
        assert False, str(e)


class TestTools(object):
    
    @classmethod
    def setup_class(cls):
        helpers.reset_db()
        
        # Test code should use CKAN's plugins.load() function to load plugins
        # to be tested.
        if not ckan.plugins.plugin_loaded('jsonschema'):
            ckan.plugins.load('jsonschema')


    # TODO
    # Test plugin/handled_resource_types


    # TODO 
    # Test plugin/handled_dataset_types



    def test_get_schema_of(self):

        for format in _c.SUPPORTED_DATASET_FORMATS:
            schema = _t.get_schema_of(format)
            
            assert schema is not None
            
            # We want to check that the result is dumpable; if it fails, it is catched 
            json.dumps(schema)


    def test_get_template_of(self):

        schema_types = ['resource-dataset', 'not-found']

        for schema_type in schema_types:

            template = _t.get_template_of(schema_type)

            if schema_type in _c.SUPPORTED_RESOURCE_FORMATS:

                # Templates are optional, can be None but should not break
                json.dumps(template)
                assert template is not None

            else:
                assert template is None
        

    # def test_get_module_for(self):

    #     schema_type = "iso"
    #     # Modules are optional, can be None but should not break
    #     module = _t.get_module_for(schema_type)

    #     assert module


    def test_get_body(self, dataset_with_extras):
        _test_getter(dataset_with_extras, _t.get_body)


    def test_get_type(self, dataset_with_extras):
        _test_getter(dataset_with_extras, _t.get_type)


    def test_get_version(self, dataset_with_extras):
        _test_getter(dataset_with_extras, _t.get_version)


    def test_get_opt(self, dataset_with_extras):
        _test_getter(dataset_with_extras, _t.get_opt)


    def test_body_of_resource_is_correct_for_jsonschema(self, dataset_with_extras):
        
        resource = conftest._get_jsonschema_resource(dataset_with_extras)   
        payload = _t.get_body(dataset_with_extras.get('id'), resource.get('id')) 

        assert payload == json.loads(resource[_c.SCHEMA_BODY_KEY])