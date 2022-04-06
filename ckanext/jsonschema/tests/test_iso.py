"""Tests for iso.py."""

import datetime
import json
import os

import ckan.lib.base as base
import ckan.plugins
import ckan.plugins.toolkit as toolkit
import ckan.tests.helpers as helpers
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.utils as _u
import pytest
from ckanext.jsonschema.logic.actions import validate_metadata, clone_metadata
import ckanext.jsonschema.configuration as configuration

@pytest.fixture
def iso19139_sample(datadir):
    return open(os.path.join(str(datadir), 'iso19139_sample.xml')).read()

@pytest.fixture
def iso_sample(datadir):
    return open(os.path.join(str(datadir), 'iso_sample.json')).read()

@pytest.fixture
def iso_wayback_sample(datadir):
    return open(os.path.join(str(datadir), 'iso_wayback_sample.xml')).read()

# Runs before each test
@pytest.fixture(autouse=True)
def reset_db():
    helpers.reset_db()

def _render_wayback(schema_body, package):
    return _t.render_template('iso/iso19139.xml', extra_vars={'metadata': schema_body, 'pkg': package})

class TestIso(object):
    
    @classmethod
    def setup_class(cls):
        
        # Test code should use CKAN's plugins.load() function to load plugins
        # to be tested.

        _plugins = ['jsonschema_iso', 'jsonschema' ]

        for plugin in _plugins:
            if not ckan.plugins.plugin_loaded(plugin):
                ckan.plugins.load(plugin)

        _t.initialize()

    def _get_default_context(self):
        return {"user": helpers.call_action("get_site_user")["name"]}


    def _create_iso_package(self, organization, iso19139_sample):

        _type = 'iso19139'
        body = _u.xml_to_json(iso19139_sample)
    
        opt = dict(_c.SCHEMA_OPT)
        opt.update({
            'validation': False,
            'imported' : True,
            'source_format':'xml',
            'source_url': "localhost:test",
            'imported_on': str(datetime.datetime.now())
        })


        # IMPORT - PREPROCESSING -
        import_context = {
            _c.SCHEMA_BODY_KEY: _t.as_dict(body),
            _c.SCHEMA_TYPE_KEY : _type,
            _c.SCHEMA_OPT_KEY : opt
        }

        package_dict = {
            # IMPORTER_TYPE = 'iso19139'old
            'type': _type,
            'owner_org': organization.get('id'),
            'license_id': 'notspecified'
        }

        errors = []
        plugin = configuration.get_plugin(_type)
        extractor = plugin.get_input_extractor(_type, import_context) 
        extractor(package_dict, errors, import_context)   

        opt['validation'] = False  
        _t.update_extras_from_context(package_dict, import_context)


        context = self._get_default_context()
        package = toolkit.get_action('package_create')(context, package_dict)
        return package



    def test_dump_package_create(self, organization, iso19139_sample, iso_sample):

        context = self._get_default_context()
        package = self._create_iso_package(organization, iso19139_sample)
                

        # test jsonschema_body
        iso_sample = json.loads(iso_sample)
        schema_body = [json.loads(extra['value']) for extra in package['extras'] if extra['key'] == _c.SCHEMA_BODY_KEY][0]

        assert iso_sample == schema_body


        # test that package  is created with correctly extracted information
        body = _u.xml_to_json(iso19139_sample)
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


    def test_dump_to_output_xml(self, organization, iso19139_sample, iso_wayback_sample):

        """
        Test for the Wayback functionality
            We cannot test the wayback on a real case scenario:
                
                input iso19139.xml -> * inserted into ckan * -> wayback

            because the wayback we construct has necessarily some big differences:
            - we use a fixed header for the XML regardless of the original xml
            - we added a <processStep> block that isn't always present
            - source XML often have empty attributes that we don't put back in the wayback

            To make this test possible:
            - we imported an iso19139 sample into CKAN
            - we made the wayback of that (iso19139_sample.xml)
                In this way, we have an iso19139 sample that respects our wayback structure
            - We imported the wayback into CKAN 
            - We conduct the test between:
                a) runtime generated wayback 
                b) the wayback that as been extracted manually from that metadata and stored into a fixture (iso_wayback_sample.xml)

            Also, we need to remove some blocks before the comparison (e.g. generated dates)
        """
    
        import re
        from six import PY3

        #### Create the package 
        package = self._create_iso_package(organization, iso19139_sample)
        schema_body = [json.loads(extra['value']) for extra in package['extras'] if extra['key'] == _c.SCHEMA_BODY_KEY][0]


        #### Get the runtime wayback
        wayback = _render_wayback(schema_body, package)
        

       #### Adjust the wayback and the sample before comparison
        
        # remove all whitespaces, \r, \n ...
        wayback = "".join(wayback.split())
        iso_wayback_sample = "".join(iso_wayback_sample.split())

        regexes = []

        # remove date blocks before the comparison as the timestamp would never match
        _regex = """
                <gmd:processStep>
                    <gmd:LI_ProcessStep>
                        <gmd:description>
                            <gco:CharacterString>Last Updated<\/gco:CharacterString>
                        <\/gmd:description>
                        <gmd:dateTime>
                            <gco:DateTime>.*<\/gco:DateTime>
                        <\/gmd:dateTime>
                    <\/gmd:LI_ProcessStep>
                <\/gmd:processStep>
                """
        regexes.append(_regex)
                    
        _regex = """
            <gmd:dateStamp>
                <gco:DateTime>.*</gco:DateTime>
            </gmd:dateStamp>
        """
        regexes.append(_regex)

        for regex in regexes:
            regex = "".join(regex.split())
            wayback = re.sub(regex, '', wayback)
            iso_wayback_sample = re.sub(regex, '', iso_wayback_sample)


        if not PY3:
            iso_wayback_sample = unicode(iso_wayback_sample, 'utf-8')

        #### Perform test
        assert wayback == iso_wayback_sample
 

    def test_validate_api_for_iso(self, organization, iso19139_sample):
        
        context = self._get_default_context()
        package = self._create_iso_package(organization, iso19139_sample)
        
        data_dict = {
            'id': package['id']
        }

        # if valid result is None, else ValidationError is raised
        result = validate_metadata(context, data_dict)

        assert result is None

    
    def test_clone_api_for_iso(self, organization, iso19139_sample):
        
        context = self._get_default_context()
        package = self._create_iso_package(organization, iso19139_sample)
        
        data_dict = {
            'id': package['id'],
            'owner_org': package['owner_org']
        }

        clone_metadata(context, data_dict)

