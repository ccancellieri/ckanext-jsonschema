
import logging

import ckanext.jsonschema.utils as _u
import requests
# use
# &wt=json for json response writer
# or
# &wt=python
# see https://solr.apache.org/guide/6_6/response-writers.html
from ckan.lib.search.common import SolrSettings

log = logging.getLogger(__name__)


BASE_URL = SolrSettings.get()[0].replace('/ckan', '')
DEFAULT_PARAMS = {
    'wt': 'json'
}

def init_core(core_name):

    log.info('Initializing core: {}'.format(core_name))

    if core_exists(core_name):
        log.info('Skipping already existing core: {}'.format(core_name))
        return

    core_create(core_name)
    configure_fields(core_name, 'test')
    log.info('Initialized core: {}'.format(core_name))

    
def core_exists(core_name):
    endpoint = '/{}/schema'.format(core_name)
    response = indexer_get(endpoint)
    return response.status_code != 404

def core_status(core_name):

    # TODO 
    # http://localhost:8983/solr/admin/cores?wt=json&action=STATUS&core=jsonschema_views
    # http://localhost:8983/solr/jsonschema_views/schema?wt=json
    #
    # see also https://solr.apache.org/guide/6_6/coreadmin-api.html#CoreAdminAPI-REQUESTSTATUS
    endpoint = '/admin/cores'
    
    query_params = DEFAULT_PARAMS.copy()
    params = {
        'action': 'STATUS',
        'core': core_name
    }
    query_params.update(params)
    
    return indexer_get(endpoint, params=query_params)

def core_create(core_name):
    # http://localhost:8983/solr/admin/cores?action=CREATE&name={core_name}&instanceDir={core_name}
    
    endpoint = '/admin/cores'
    query_params = DEFAULT_PARAMS.copy()
    params = {
        'configSet':'basic_configs',
        'action':'CREATE',
        'name': core_name
    }
    query_params.update(params)

    log.info('Creating core: {}'.format(core_name))

    return indexer_get(endpoint, params=params)

def core_unload(core_name, purge=False):

    endpoint = '/admin/cores'
    query_params = DEFAULT_PARAMS.copy()
    params = {
        'action':'UNLOAD',
        'core': core_name,
        'deleteInstanceDir': 'true' if purge else 'false' 
    }
    query_params.update(params)


    if purge:
        log.warn('Unloading core {} and all of its data'.format(core_name))
    else:
        log.warn('Unloading core: {}'.format(core_name))

    return indexer_get(endpoint, params=params)

def core_reindex(jsonschema_type):
    pass

def core_reindex_all():
    # for _type in register.types:
    #     reindex(_type)
    pass

def get_indexer_representation(jsonschema_type, data):
    '''
    '''
    
    plugin = get_plugin()
    return plugin.get_indexer_representation(data) # flat result
     

def update(core_name, data):

    data = {

    }


    # TODO dict must be flat (defined by an interface method (By jsonschema_type))
    pass

# TODO define interface IBinder?
def configure_fields(core_name, jsonschema_type):

    endpoint = '/{}/schema'.format(core_name)
    
    data = {
        "add-field": [
            # { 
            #     "name":"id",
            #     "type":"string",
            #     "stored": True 
            # },
            { 
                "name":"name",
                "type":"string",
                "stored": True 
            },
            { 
                "name":"description",
                "type":"string",
                "stored": True 
            },
            { 
                "name":"type",
                "type":"string",
                "stored": True 
            }
        ]
    }

    # data = {
    #     "add-field":[
    #         { 
    #             "name":"shelf",
    #             "type":"myNewTxtField",
    #             "stored": True 
    #         },
    #         { 
    #             "name":"location",
    #             "type":"myNewTxtField",
    #             "stored":True 
    #         }
    #     ]
    # }

    return indexer_post(endpoint, data)

    # To add a new field to the schema, follow this example from the Bash prompt:

    # $ curl -X POST -H 'Content-type:application/json' --data-binary '{
    # "add-field":{
    #     "name":"new_example_field",
    #     "type":"text_general",
    #     "stored":true }
    # }' https://..../api/collections/jsonschema_views/schema

    # {
    # "add-field":[
    #     { "name":"shelf",
    #     "type":"myNewTxtField",
    #     "stored":true },
    #     { "name":"location",
    #     "type":"myNewTxtField",
    #     "stored":true }]
    # }

    # NOTE: these configurations can be part of the REGISTRY config??

    # see https://solr.apache.org/guide/6_6/schema-api.html#SchemaAPI-EXAMPLES
    # http://localhost:8983/solr/gettingstarted/schema

    

def search(core_name):
    ''' 
        - We need a query by id (single result) 
        - We need a free text like query in each field
    '''
    pass


def indexer_get(url, params={}):

    url = BASE_URL + url
    return requests.get(url, params)


def indexer_post(url, payload={}):
    
    import json
    payload = json.dumps(payload)
    
    url = BASE_URL + url

    response = requests.post(url, payload) 
    content = json.loads(response.content) 

    if 'errors' in content:
        log.error('Errors during POST to indexer')
        log.error('URL: {}'.format(url))
        log.error('Payload: {}'.format(payload))
        log.error('Errors: {}'.format(content['errors']))

    return response