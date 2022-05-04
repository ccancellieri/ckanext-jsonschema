"""Tests for iso.py."""

import datetime
import json
import os

import ckan.plugins
import ckan.plugins.toolkit as toolkit
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
from ckan.lib.helpers import url_for
import ckanext.jsonschema.configuration as configuration
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.utils as _u
import pytest
from ckanext.jsonschema.logic.actions import clone_metadata, validate_metadata
from six import text_type
import uuid

@pytest.fixture
def iso19139_sample(datadir):
    return open(os.path.join(str(datadir), 'iso19139_sample.xml')).read()

@pytest.fixture
def iso_sample(datadir):
    return open(os.path.join(str(datadir), 'iso_sample.json')).read()

@pytest.fixture
def iso_sample2(datadir):
    return json.loads(open(os.path.join(str(datadir), 'iso_sample2.json')).read())

@pytest.fixture
def iso_wayback_sample(datadir):
    return open(os.path.join(str(datadir), 'iso_wayback_sample.xml')).read()

# Runs before each test
@pytest.fixture(autouse=True)
def reset_db():
    helpers.reset_db()

def _render_wayback(schema_body, package):
    return __render_template('iso/iso19139.xml', extra_vars={'metadata': schema_body, 'pkg': package})

class TestIso(helpers.FunctionalTestBase):
    
    _load_plugins = ('jsonschema_iso', 'jsonschema')

    @classmethod
    def setup_class(cls):
        
        helpers.reset_db()

        _t.initialize()

        super(TestIso, cls).setup_class()

    def test_package_create_fields_are_json_and_resources_fields_are_jsons(self, iso19139_sample):

        package = self._create_iso_package_from_xml(iso19139_sample)

        assert isinstance(package[_c.SCHEMA_BODY_KEY], dict) 
        assert isinstance(package[_c.SCHEMA_OPT_KEY], dict) 
        assert isinstance(package[_c.SCHEMA_TYPE_KEY], text_type) 

        for resource in package.get('resources'):
            assert isinstance(resource[_c.SCHEMA_BODY_KEY], dict) 
            assert isinstance(resource[_c.SCHEMA_OPT_KEY], dict) 
            assert isinstance(resource[_c.SCHEMA_TYPE_KEY], text_type) 


    def test_package_create_body_is_correct(self, iso19139_sample, iso_sample):
        package = self._create_iso_package_from_xml(iso19139_sample)

        # test jsonschema_body
        iso_sample = json.loads(iso_sample)
        schema_body = _t.get_package_body(package)

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


    def test_dump_to_output_xml(self, iso19139_sample, iso_wayback_sample):

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
        package = self._create_iso_package_from_xml(iso19139_sample)
        schema_body = _t.get_package_body(package)


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


    def test_validate_api(self, iso19139_sample):
        
        context = {'user': factories.Sysadmin().get('name')}
        package = self._create_iso_package_from_xml(iso19139_sample)
        
        data_dict = {
            'id': package['id']
        }

        # if valid result is None, else ValidationError is raised
        result = validate_metadata(context, data_dict)

        assert result is None
    

    def test_clone_api_with_sysadmin(self, iso_sample2):
        '''
        Test the clone of a private metadata
        '''
        
        # Create sysadmin
        user = factories.Sysadmin()

        # Create organization 
        owner_org = factories.Organization()

        # Create the metadata in that organization
        package_dict = {
            'owner_org': owner_org.get('id'),
            'name': str(uuid.uuid4())
        }
        package_dict.update(iso_sample2)

        context = {'user': user.get('name')}
        package = toolkit.get_action('package_create')(context, package_dict)

        # Create headers and payload for the request
        headers = {'Authorization': str(user.get('apikey'))}
        data_dict = {
            'id': package['id'],
            'owner_org': owner_org['id']
        }

        # Get the app 
        app = self._get_test_app()

        # Request the clone
        response = app.post_json('/api/action/jsonschema_clone', data_dict, headers=headers)
        
        # Check if it worked
        assert response.status_int == 200

        response_body = json.loads(response)
        assert response_body['success'] == True

        # The id should be different from the source package
        cloned_id = response_body['result']['id']
        assert cloned_id != package['id']

        # Check that we can do a package show
        show_result = toolkit.get_action('package_show')(context, {'id': cloned_id})
        assert show_result != None
        

    def test_clone_api_with_editor_user(self, iso_sample2):
        # We create a package
        # Then we try to clone it by a user with edit permission on its organization, and we should succeed
        # Then we try to clone it by a user without the needed permissions, and we should fail

        
        # Create the user
        user1 = factories.User()
        user2 = factories.User()

        # Create organization with user1 as editor
        owner_org = factories.Organization(
            users=[{'name': user1.get('id'), 'capacity': 'editor'}]
        )

        # Create the metadata in that organization
        package_dict = {
            'owner_org': owner_org.get('id'),
            'name': str(uuid.uuid4())
        }
        package_dict.update(iso_sample2)

        context = {'user': user1.get('name')}

        # Create with the source package with the first user
        package = toolkit.get_action('package_create')(context, package_dict)


        # Create headers and payload for the clone request with the first user (should succeed)
        headers = {'Authorization': str(user1.get('apikey'))}
        data_dict = {
            'id': package['id'],
            'owner_org': owner_org['id']
        }

        # Get the app 
        app = self._get_test_app()

        # Request the clone
        response = app.post_json('/api/action/jsonschema_clone', data_dict, headers=headers)
        
        # Check if it worked
        assert response.status_int == 200

        response_body = json.loads(response.body)
        assert response_body['success'] == True

        # The id should be different from the source package
        cloned_id = response_body['result']['id']
        assert cloned_id != package['id']

        # Check that we can do a package show
        show_result = toolkit.get_action('package_show')(context, {'id': cloned_id})
        assert show_result != None

        # Create headers and payload for the clone request with the second user (should fail)
        headers = {'Authorization': str(user2.get('apikey'))}
        data_dict = {
            'id': package['id'],
            'owner_org': owner_org['id']
        }

        # Request the clone
        try:
            response = app.post_json('/api/action/jsonschema_clone', data_dict, headers=headers)
        except:
            pass


    def _create_iso_package_from_xml(self, iso19139_sample):
        '''
        Replicates the importer logic to create an ISO package
        '''

        _type = 'iso19139'
        body = _u.xml_to_json(iso19139_sample)
    
        opt = dict(_c.SCHEMA_OPT)
        opt.update({
            'imported' : True,
            'source_format':'xml',
            'source_url': "localhost:test",
            'imported_on': str(datetime.datetime.now())
        })


        # IMPORT - PREPROCESSING -
        import_context = {}

        package_dict = {
            # IMPORTER_TYPE = 'iso19139'old
            'type': _type,
            'owner_org': factories.Organization().get('id'),
            'license_id': 'notspecified',
            _c.SCHEMA_BODY_KEY: _t.as_dict(body),
            _c.SCHEMA_TYPE_KEY : _type,
            _c.SCHEMA_OPT_KEY : opt,
        }

        errors = []
        plugin = configuration.get_plugin(_type)
        extractor = plugin.get_input_extractor(_type, package_dict, import_context) 
        extractor(package_dict, errors, import_context)   

        opt['validation'] = False  


        context = {'user': factories.Sysadmin().get('name')}
        package = toolkit.get_action('package_create')(context, package_dict)
        return package

    # def _create_iso_package_with_jsonschema_and_dataset_resources(self, iso_sample2):
    #     '''
    #     Create an ISO package with jsonschema resources and dataset resources
    #     '''

    #     # Create sysadmin
    #     user = factories.Sysadmin()

    #     # Create organization with the user as admin
    #     owner_org = factories.Organization(
    #         users=[{'name': user.get('name'), 'capacity': 'admin'}],
    #     )
        
    #     # Create the metadata in that organization
    #     package_dict = {
    #         'owner_org': owner_org.get('id'),
    #         'name': str(uuid.uuid4())
    #     }
    #     package_dict.update(iso_sample2)

    #     context = {'user': user.get('name')}
    #     package = toolkit.get_action('package_create')(context, package_dict)
    #     return user, owner_org, package 


def __render_template(template_name, extra_vars):
    '''
    This function creates a mock jinja environment to render templates
    base.render cannot be used because there isn't a session registered when running tests
    This function shouldn't be used outside of tests
    '''

    import os

    import jinja2

    # setup for render
    templates_paths = [
        os.path.join(_c.PATH_ROOT, "jsonschema/templates"),
        os.path.join(_c.PATH_ROOT, "jsonschema/iso19139/templates"), #TODO should get from plugins
    ]
    templateLoader = jinja2.FileSystemLoader(searchpath=templates_paths)
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(template_name)
    
    # add helpers
    from ckan.plugins import get_plugin
    h = get_plugin(_c.TYPE).get_helpers()
    extra_vars['h'] = h

    try:
        return template.render(extra_vars)
    except jinja2.TemplateSyntaxError as e:
        pass
        #log.error('Unable to interpolate line \'{}\'\nError:{}'.format(str(e.lineno), str(e)))
    except Exception as e:
        pass
        #log.error('Exception: {}'.format(str(e)))
