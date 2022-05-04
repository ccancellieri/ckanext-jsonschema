"""Tests for dataset interactions."""


import ckan.plugins
import ckan.plugins.toolkit as toolkit
import ckan.tests.helpers as helpers
import ckanext.jsonschema.tools as _t
import pytest
import uuid

# Runs before each test
@pytest.fixture(autouse=True)
def reset_db():
    helpers.reset_db()

class TestDataset(object):
    
    @classmethod
    def setup_class(cls):
        
        # Test code should use CKAN's plugins.load() function to load plugins
        # to be tested.

        _plugins = ['jsonschema_dataset', 'jsonschema_iso', 'jsonschema' ]

        for plugin in _plugins:
            if not ckan.plugins.plugin_loaded(plugin):
                ckan.plugins.load(plugin)

        _t.initialize()

    def _get_default_context(self):
        return {"user": helpers.call_action("get_site_user")["name"]}

    def test_package_create_dataset(self, organization):
        
        package_dict = {
            'owner_org': organization.get('id'),
            'type': 'dataset',
            'name': str(uuid.uuid4())
        }

        package_dict.update({})

        context = self._get_default_context()
        package = toolkit.get_action('package_create')(context, package_dict)
        return package

    def test_package_create_dataset_with_dataset_resources(self):
        assert True

    def test_package_create_dataset_with_dataset_and_jsonschema_resources(self):
        assert True

    def test_package_create_jsonschema_resources_fields_are_jsons(self):
        assert True

    def test_clone_api_with_sysadmin(self):
        # use also json resource and test its content, check id its different
        assert True

    def test_clone_api_with_normal_user(self):
        assert True