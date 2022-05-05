"""Tests for dataset interactions."""


import os
import uuid

import ckan.plugins.toolkit as toolkit
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
import ckanext.jsonschema.tools as _t
import pytest


# Runs before each test
@pytest.fixture(autouse=True)
def reset_db():
    helpers.reset_db()

@pytest.fixture
def dataset_sample(datadir):
    return open(os.path.join(str(datadir), 'dataset_sample.json')).read()

@pytest.fixture
def dataset_sample2(datadir):
    return open(os.path.join(str(datadir), 'dataset_sample2.json')).read()


class TestDataset(helpers.FunctionalTestBase):

    _load_plugins = ('jsonschema_dataset', 'jsonschema_iso', 'jsonschema')
    
    @classmethod
    def setup_class(cls):
        
        helpers.reset_db()
        _t.initialize()
        super(TestDataset, cls).setup_class()

        cls.app = cls._get_test_app()


    def _get_default_context(self):
        return {"user": helpers.call_action("get_site_user")["name"]}

    def test_package_create_dataset(self, organization, dataset_sample):
        
        package_dict = {
            'owner_org': organization.get('id'),
            'name': str(uuid.uuid4())
        }

        package_dict.update(dataset_sample)

        context =  {'user': factories.Sysadmin().get('name')}
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
