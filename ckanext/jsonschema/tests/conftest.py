# https://docs.pytest.org/en/6.2.x/fixture.html#requesting-fixtures
# Fixtures in this file are automatically discovered by Pytest
#
# If there exist a fixture called user, e.g:
#
# @pytest.fixture
# def user():
#   return factories.User()
#
# Any method can declare a parameter user, and Pytest will call the fixture and provide the result

import os
from distutils import dir_util

import ckan.tests.factories as factories
import pytest


@pytest.fixture
def datadir(tmpdir, request):
    '''
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    '''
    from six import PY3

    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        if PY3:
            dir_util.copy_tree(test_dir, str(tmpdir))
        else:
            dir_util.copy_tree(test_dir, bytes(tmpdir))

    return tmpdir


@pytest.fixture
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
                }
            ],
            
    }


    return factories.Dataset(**body)


def get_jsonschema_resource(dataset):

    resource_body = {
        'package_id' : dataset.get('id'),
        'format': 'csv',
        'jsonschema_type': 'resource-dataset',
        'jsonschema_body': '{\"name\":\"\", \"description\": \"\"}',
        'jsonschema_opt': '{ \"key\": \"value\"}'
    }  

    resource = factories.Resource(**resource_body)
    return resource
