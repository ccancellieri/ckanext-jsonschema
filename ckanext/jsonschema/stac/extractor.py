import json
import uuid

import ckan.lib.helpers as h
import ckan.lib.munge as munge
import ckanext.jsonschema.constants as _jsonschema_c
import ckanext.jsonschema.validators as _v
from ckanext.jsonschema.stac import constants as _c


# TODO
# Eventually refactor in StacExtractor -> ItemExtractor, CatalogExtractor, CollectionExtractor

def _extract_id(dataset_type, body):
    if dataset_type == _c.TYPE_STAC:
        return body.get('id')


def _extract_json_name(body, type, opt, version, data, errors, context):
    
    name = _extract_id(type, body)
    
    if not name:
        name = str(uuid.uuid4())
    else:
        name = munge.munge_name(name)

    body['id'] = name
    
    _dict = {
        'name': name, 
        'url': h.url_for(controller='package', action='read', id=name, _external=True)
       }
    data.update(_dict)

#### COMMON ####

################

##### ITEM ##### 

def _extract_item_from_json(body, type, opt, version, data, errors, context):
    
    try:
        _extract_json_name(body, type, opt, version, data, errors, context)
        _extract_item_json_body(body, type, opt, version, data, errors, context)
        _extract_json_resources(body, type, opt, version, data, errors, context)

    except Exception as e:
        _v.stop_with_error(('Error decoding metadata identification: {}').format(str(e)), 'metadata identifier', errors)

    return (body, type, opt, version, data)

def _extract_item_json_body(body, type, opt, version, data, errors, context):
    
    _dict = {}    

    properties = body.get('properties')

    if properties:
        _dict = {
            'title': properties.get('title'),
            'notes': properties.get('description'),
            'license_id': properties.get('license')
            #'metadata_modified': properties.get('updated'),
            #'metadata_created': properties.get('created'),
        }

    version = body.get('stac_version')
    if version:
        _dict['version'] = version

    if _dict: 
        data.update(_dict)

def _extract_json_resources(body, type, opt, version, data, errors, context):
    """
    This methods extract the resources from the body of the stac-item (which are in a domain-specific position)
    and stores them in the "resources" field of the data, so that they can be processed later by the
    resource_extractor validator
    """

    # We use pop so that the assets are not retained in the original body, because we are going
    # to use them as resources
    _assets = body.pop('assets', {})
    _resources = []

    for _asset_role in _assets:

        _asset = {_asset_role: _assets[_asset_role]}
        _name = _asset[_asset_role].get('title')
        _mimetype = _asset[_asset_role].get('type')

        _url = _asset[_asset_role].get('href')
        if _url:
            # if there is an href in the asset, we remove it from the json so it can be consistentely
            # be managed using the resource field "url"
            _asset[_asset_role].pop('href')

        
        _new_resource_dict = {
            _jsonschema_c.SCHEMA_OPT_KEY: json.dumps(opt),
            _jsonschema_c.SCHEMA_VERSION_KEY: version,
            _jsonschema_c.SCHEMA_BODY_KEY: _asset,
            _jsonschema_c.SCHEMA_TYPE_KEY: _c.TYPE_STAC_RESOURCE,
            'url': _url,
            'name': _name,
            'mimetype': _mimetype
        }

        _resources.append(_new_resource_dict)
  
    data.update({'resources': _resources})


##################

##### CATALOG ##### 

def _extract_catalog_from_json(body, type, opt, version, data, errors, context):
    
    try:
        _extract_json_name(body, type, opt, version, data, errors, context)
        _extract_catalog_json_body(body, type, opt, version, data, errors, context)

    except Exception as e:
        _v.stop_with_error(('Error decoding metadata identification: {}').format(str(e)), 'metadata identifier', errors)

    return (body, type, opt, version, data)


def _extract_catalog_json_body(body, type, opt, version, data, errors, context):
    
    _dict = {
        'title': body.get('title'),
        'notes': body.get('description'),
        'license_id': body.get('license'),
        'version': body.get('stac_version')
    }

    data.update(_dict)


######################

##### COLLECTION ##### 

def _extract_collection_from_json(body, type, opt, version, data, errors, context):
    
    try:
        _extract_json_name(body, type, opt, version, data, errors, context)
        _extract_collection_json_body(body, type, opt, version, data, errors, context)

    except Exception as e:
        _v.stop_with_error(('Error decoding metadata identification: {}').format(str(e)), 'metadata identifier', errors)

    return (body, type, opt, version, data)


def _extract_collection_json_body(body, type, opt, version, data, errors, context):
    
    _dict = {
        'title': body.get('title'),
        'notes': body.get('description'),
        'license_id': body.get('license'),
        'version': body.get('stac_version')
    }
    data.update(_dict)

    
    # KEYWORDS
    if 'tags' not in data:
        data['tags'] = []

    keywords = body.get('keywords', [])
                
    for keyword in keywords:
        data['tags'].append({'name': munge.munge_tag(keyword)})
        



    return (body, type, opt, version, data)
