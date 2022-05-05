"""Tests for dataset interactions."""


import json
import os
import uuid

import ckan.plugins.toolkit as toolkit
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
import ckanext.jsonschema.constants as _c
import pytest
from six import text_type

from logging import getLogger
log = getLogger(__name__)


# Runs before each test
@pytest.fixture(autouse=True)
def reset_db():
    helpers.reset_db()

@pytest.fixture
def dataset_sample(datadir):
    return json.loads(open(os.path.join(str(datadir), 'dataset_sample.json')).read())

@pytest.fixture
def dataset_sample2(datadir):
    return json.loads(open(os.path.join(str(datadir), 'dataset_sample2.json')).read())


@pytest.fixture
def dataset_sample3(datadir):
    return json.loads(open(os.path.join(str(datadir), 'dataset_sample3.json')).read())


@pytest.mark.ckan_config("ckan.plugins", "jsonschema_dataset jsonschema_iso jsonschema")
@pytest.mark.usefixtures("with_plugins")
class TestDataset(object):

    ############ Functional Tests - API ############

    def test_clone_api_with_sysadmin(self, dataset_sample3, app):
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
        package_dict.update(dataset_sample3)

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

        source_json_resource = dataset_sample3['resources'][0][_c.SCHEMA_BODY_KEY]
        cloned_json_resource = show_result['resources'][0]['jsonschema_body']

        # we need json.loads because of a bug on the package_show that returns the resources as strings
        # instead of dicts
        assert json.loads(cloned_json_resource) == source_json_resource

        
    def test_clone_api_with_normal_user(self, dataset_sample3, app):
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
        package_dict.update(dataset_sample3)

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

    ################################################


    def test_package_create_dataset(self, organization, dataset_sample):
        
        package_dict = {
            'owner_org': organization.get('id'),
            'name': str(uuid.uuid4())
        }

        package_dict.update(dataset_sample)

        context =  {'user': factories.Sysadmin().get('name')}
        package = toolkit.get_action('package_create')(context, package_dict)
        return package


    def test_package_create_dataset_with_dataset_and_jsonschema_resources(self, organization, dataset_sample2):
        
        package_dict = {
            'owner_org': organization.get('id'),
            'name': str(uuid.uuid4())
        }

        package_dict.update(dataset_sample2)

        context =  {'user': factories.Sysadmin().get('name')}
        package = toolkit.get_action('package_create')(context, package_dict)
        return package


    def test_jsonschema_resources_fields_are_jsons_in_package_show(self, organization, dataset_sample2):


        package_dict = {
            'owner_org': organization.get('id'),
            'name': str(uuid.uuid4())
        }

        package_dict.update(dataset_sample2)

        context =  {'user': factories.Sysadmin().get('name')}
        package = toolkit.get_action('package_create')(context, package_dict)
        package = toolkit.get_action('package_show')(context, {'id': package['id']})


        # This is a dataset, shouldn't have jsonschema fields
        assert _c.SCHEMA_BODY_KEY not in package
        assert _c.SCHEMA_OPT_KEY not in package  
        assert _c.SCHEMA_TYPE_KEY not in package

        for resource in package.get('resources'):
            if _c.SCHEMA_TYPE_KEY in resource:
                assert isinstance(resource[_c.SCHEMA_BODY_KEY], dict) 
                assert isinstance(resource[_c.SCHEMA_OPT_KEY], dict) 
                assert isinstance(resource[_c.SCHEMA_TYPE_KEY], text_type) 


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