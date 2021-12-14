# https://docs.pytest.org/en/6.2.x/fixture.html#requesting-fixtures
# Fixtures in this file are automatically discovered by Pytest
#
# If there exist a fixture called user, e.g:
#
# @pytest.fixture()
# def user():
#   return factories.User()
#
# Any method can declare a parameter user, and Pytest will call the fixture and provide the result

import pytest
import ckan.tests.factories as factories


@pytest.fixture()
def organization():
    return factories.Organization()


@pytest.fixture
def dataset_with_extras(organization):

    body = {
            'owner_org': organization['id'],
            'extras' : [
                {
                    'key': 'jsonschema_body',
                    'value': '{}'
                },
                {
                    'key': 'jsonschema_type',
                    "value": "jsonschema"
                },
                {    
                    "key": "jsonschema_opt",
                    "value": '{ \"key\": \"value\"}'
                },
                {    
                    "key": "jsonschema_version",
                    "value": '1'
                }  
            ],
            
    }


    return factories.Dataset(**body)


def _get_jsonschema_resource(dataset):

    resource_body = {
        'package_id' : dataset.get('id'),
        'format': 'csv',
        'jsonschema_type': 'resource-dataset',
        'jsonschema_body': '{\"name\":\"\", \"description\": \"\"}',
        'jsonschema_opt': '{ \"key\": \"value\"}',
        'jsonschema_version': '1'
    }  

    resource = factories.Resource(**resource_body)
    return resource
