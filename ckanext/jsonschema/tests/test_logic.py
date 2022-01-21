"""Tests for iso.py."""

import os

import ckan.plugins
import ckan.tests.helpers as helpers
import pytest
from ckanext.jsonschema.logic.get import get_pkg


@pytest.fixture
def iso19139_sample(datadir):
    return open(os.path.join(str(datadir), 'iso19139_sample.xml')).read()

class TestLogic(object):
    
    @classmethod
    def setup_class(cls):
        helpers.reset_db()
        
        # Test code should use CKAN's plugins.load() function to load plugins
        # to be tested.

        _plugins = ['jsonschema', 'jsonschema_iso', 'jsonschema_iso19139']

        for plugin in _plugins:
            if not ckan.plugins.plugin_loaded(plugin):
                ckan.plugins.load(plugin)


    def test_get_pkg(self, dataset_with_extras):

        try:
            get_pkg('')
        except Exception:
            assert True

        pkg = get_pkg(dataset_id=dataset_with_extras['id'])

        assert type(pkg) is dict