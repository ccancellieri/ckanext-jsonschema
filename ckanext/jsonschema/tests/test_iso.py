"""Tests for iso.py."""

import datetime
import json
import os
import uuid

import ckan.lib.base as base
import ckan.plugins.toolkit as toolkit
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
import ckanext.jsonschema.configuration as configuration
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.utils as _u
import pytest
from six import text_type

from logging import getLogger
log = getLogger(__name__)


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

@pytest.fixture
def iso_template(datadir):
    return json.loads(open(os.path.join(str(datadir), 'iso_template.json')).read())


@pytest.fixture
def json_resource(datadir):
    return json.loads(open(os.path.join(str(datadir), 'json_resource.json')).read())

@pytest.fixture
def dataset_resource(datadir):
    return json.loads(open(os.path.join(str(datadir), 'dataset_resource.json')).read())


# Runs before each test
@pytest.fixture(autouse=True)
def reset_db():
    helpers.reset_db()

def _render_wayback(schema_body, package):
    return base.render('iso/iso19139.xml', extra_vars={'metadata': schema_body, 'pkg': package})

@pytest.mark.ckan_config("ckan.plugins", "jsonschema_dataset jsonschema_iso jsonschema")
@pytest.mark.usefixtures("with_plugins")
class TestIso(object):

    ############ Functional Tests - API ############
    
    
    def test_validate_api(self, iso_sample2, app):
        
        # Create the user
        user1 = factories.User()

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

        # Request the validate
        response = self.__do_post(app, 
            '/api/action/jsonschema_validate', 
            data=data_dict,
            headers=headers
        )
        
        response_body = json.loads(response.body)
        assert response_body['success'] == True

    
    def test_clone_api_with_sysadmin(self, iso_sample2, app):
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

        # Request the clone
        response = self.__do_post(app, 
            '/api/action/jsonschema_clone', 
            data=data_dict,
            headers=headers
        )
        
        response_body = json.loads(response.body)
        assert response_body['success'] == True

        # The id should be different from the source package
        cloned_id = response_body['result']['id']
        assert cloned_id != package['id']

        # Check that we can do a package show
        show_result = toolkit.get_action('package_show')(context, {'id': cloned_id})
        assert show_result != None


    def test_clone_api_with_editor_user(self, iso_sample2, app):
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

        # Request the clone
        response = self.__do_post(app, 
            '/api/action/jsonschema_clone', 
            data=data_dict,
            headers=headers
        )

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
             # Request the clone
            response = self.__do_post(app, 
                '/api/action/jsonschema_clone', 
                data=data_dict,
                headers=headers
            )     
        # except webtest.app.AppError as e:
        except Exception as e:
            # Testing the string message is not very reliable, but we need to be sure that the
            # error is 403 and not anything else, and there isn't the response status in the object
            log.info(e.message)
            if e.message.startswith('Bad response: 403'):
                assert True
            else:
                assert False


    @pytest.mark.usefixtures("with_request_context")
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

    
    def test_package_create_fields_are_json_and_resources_fields_are_jsons(self, iso_sample2):


        # Create sysadmin
        user = factories.Sysadmin()

        # Create organization with the user as admin
        owner_org = factories.Organization(
            users=[{'name': user.get('name'), 'capacity': 'admin'}],
        )
        
        # Create the metadata in that organization
        package_dict = {
            'owner_org': owner_org.get('id'),
            'name': str(uuid.uuid4())
        }
        package_dict.update(iso_sample2)

        context = {'user': user.get('name')}
        package = toolkit.get_action('package_create')(context, package_dict)
        package = toolkit.get_action('package_show')(context, {'id': package['id']})

        assert isinstance(package[_c.SCHEMA_BODY_KEY], dict) 
        assert isinstance(package[_c.SCHEMA_OPT_KEY], dict) 
        assert isinstance(package[_c.SCHEMA_TYPE_KEY], text_type) 

        for resource in package.get('resources'):
            if _c.SCHEMA_TYPE_KEY in resource:
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
        # Now the package description is dinamically generated, so it won't exactly match the source description
        # but we can check that the source is included into the generated
        notes = data_identification['gmd:abstract']['gco:CharacterString']
        #assert notes == package.get('notes')
        assert notes in package.get('notes')        


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

   
    def test_empty_iso_add_resources_delete_resources_delete_dataset(self, iso_template, dataset_resource, json_resource):
        """
        Creates a package without resources
        Add a dataset resource and a jsonschema resource
        Delete all resources
        Delete the package
        """

        user1 = factories.User()

        # Create organization with user1 as editor
        owner_org = factories.Organization(
            users=[{'name': user1.get('id'), 'capacity': 'editor'}]
        )

        # Create the metadata in that organization
        package_dict = {
            'owner_org': owner_org.get('id'),
            'name': str(uuid.uuid4()),
            'type': 'iso',
            _c.SCHEMA_TYPE_KEY: 'iso',
            _c.SCHEMA_BODY_KEY: iso_template,
            _c.SCHEMA_OPT_KEY: {}
        }

        context = {'user': user1.get('name')}

        # Create with the source package with the first user
        package = toolkit.get_action('package_create')(context, package_dict)

        # Add a new resource
        dataset_resource.update({'package_id': package.get('id')})
        json_resource.update({'package_id': package.get('id')})
        
        toolkit.get_action('resource_create')(context, dataset_resource)
        toolkit.get_action('resource_create')(context, json_resource)

        package = toolkit.get_action('package_show')(context, {'id': package.get('id')})

        # Delete resources
        for resource in package.get('resources'):
            toolkit.get_action('resource_delete')(context, resource)

        package = toolkit.get_action('package_show')(context, {'id': package.get('id')})

        # All resources have been deleted
        assert len(package.get('resources')) == 0

        # Package has been deleted
        toolkit.get_action('package_delete')(context, {'id': package.get('id')})
        package = toolkit.get_action('package_show')(context, {'id': package.get('id')})

        assert package.get('state') == 'deleted'


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


    def _create_iso_package_with_jsonschema_and_dataset_resources(self, iso_sample2):
        '''
        Create an ISO package with jsonschema resources and dataset resources
        '''

        # Create sysadmin
        user = factories.Sysadmin()

        # Create organization with the user as admin
        owner_org = factories.Organization(
            users=[{'name': user.get('name'), 'capacity': 'admin'}],
        )
        
        # Create the metadata in that organization
        package_dict = {
            'owner_org': owner_org.get('id'),
            'name': str(uuid.uuid4())
        }
        package_dict.update(iso_sample2)

        context = {'user': user.get('name')}
        package = toolkit.get_action('package_create')(context, package_dict)
        return user, owner_org, package 


    def __do_post(self, app, url, data, headers):
        '''
        Needed to run the tests in local environment
        The code to run posts is different between CKAN 2.8.6 (local) and CKAN 2.9.5 (pipeline)
        The try block should work on the latter
        The responses have different shapes
        '''
        
        try:
            response = app.post(
                url, 
                data=data,
                headers=headers
            )
        except:
            response = app.post_json(
                url, 
                data,
                headers=headers
            )

        return response