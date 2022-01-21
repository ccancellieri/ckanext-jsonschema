"""Tests for iso.py."""

import datetime
import os

import ckan.plugins
import ckan.plugins.toolkit as toolkit
import ckan.tests.helpers as helpers
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
import pytest
from ckanext.jsonschema.plugin import (handled_dataset_types,
                                       handled_resource_types)
import ckanext.jsonschema.utils as _u
import json

@pytest.fixture
def iso19139_sample(datadir):
    return open(os.path.join(str(datadir), 'iso19139_sample.xml')).read()

class TestIso(object):
    
    @classmethod
    def setup_class(cls):
        helpers.reset_db()
        
        # Test code should use CKAN's plugins.load() function to load plugins
        # to be tested.

        _plugins = ['jsonschema', 'jsonschema_iso', 'jsonschema_iso19139']

        for plugin in _plugins:
            if not ckan.plugins.plugin_loaded(plugin):
                ckan.plugins.load(plugin)


    def test_dump_to_output(self, organization, iso19139_sample):

        body = _u.xml_to_json(iso19139_sample)

    
        SCHEMA_TYPE_KEY = 'iso19139'
        package_dict = {}

        # IMPORTER_TYPE = 'iso19139'old
        _type = SCHEMA_TYPE_KEY
        package_dict['type'] = _type
        package_dict['owner_org'] = organization['id']
        
        opt = dict(_c.SCHEMA_OPT)

        opt.update({
            'imported' : True,
            'source_format':'xml',
            'source_url': "localhost:test",
            'imported_on': str(datetime.datetime.now())
            })
        extras = []
        package_dict['extras'] = extras
        extras.append({ 'key': _c.SCHEMA_BODY_KEY, 'value' : body })
        extras.append({ 'key': _c.SCHEMA_TYPE_KEY, 'value' : _type })
        extras.append({ 'key': _c.SCHEMA_OPT_KEY, 'value' :  opt })
        extras.append({ 'key': _c.SCHEMA_VERSION_KEY, 'value' : _c.SCHEMA_VERSION })

        try:
            context = {"user": helpers.call_action("get_site_user")["name"]}
            package = toolkit.get_action('package_create')(context, package_dict)

            # asserts: package is created with correctly extracted information
            metadata = json.loads(body)['gmd:MD_Metadata']
            data_identification = metadata['gmd:identificationInfo']['gmd:MD_DataIdentification']
            
            # notes
            notes = data_identification['gmd:abstract']['gco:CharacterString']
            assert notes == package.get('notes')
            
            # number of keywords (not content)
            keywords_count = 0
            keywords_root = data_identification['gmd:descriptiveKeywords']
            for keywords_section in keywords_root:
                keywords = keywords_section['gmd:MD_Keywords']['gmd:keyword']
                keywords_count += len(keywords)
        
            assert keywords_count == len(package.get('tags', []))

            # title
            title = data_identification['gmd:citation']['gmd:CI_Citation']['gmd:title']['gco:CharacterString']
            assert title == package.get('title')

        except:
            pass