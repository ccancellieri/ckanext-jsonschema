import json
import uuid

import ckan.lib.helpers as h
import ckan.lib.munge as munge
import ckanext.jsonschema.constants as _jsonschema_c
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.validators as _v
from ckanext.jsonschema.logic.actions import importer
from ckanext.jsonschema.stac import constants as _c


def extract_id(dataset_type, body):
        if dataset_type == _c.TYPE_STAC:
            return body.get('id')

class StacExtractor():

    def extract_from_json(self, data, errors, context):
        
        try:
            self._extract_json_name(data, errors, context)
            self._extract_json_body(data, errors, context)

        except Exception as e:
            _v.stop_with_error(str(e), 'extract_from_json', errors)


    def _extract_json_name(self, data, errors, context):
        
        body = _t.get_context_body(context)
        _type = _t.get_context_type(context)

        name = self._extract_id(_type, body)
        
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


    def _extract_id(self,dataset_type, body):
        return extract_id(dataset_type, body)

    def _extract_json_body(self, data, errors, context):
        raise NotImplementedError("Please Implement this method ")



class ItemExtractor(StacExtractor):

    def _extract_json_body(self, data, errors, context):
        
        body = _t.get_context_body(context)

        _dict = {}    

        properties = body.get('properties')

        if properties:
            _dict = {
                'title': properties.get('title') or body.get('id'),
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

    def assets_to_resources(self, data, errors, context):
        '''
        This methods extract the resources from the body of the stac-item (which are in a domain-specific position)
        and stores them in the "resources" field of the data, so that they can be processed later by the
        resource_extractor validator
        '''

        body = _t.get_context_body(context)
        opt = _t.get_context_opt(context)

        _assets = {}
        if 'assets' in body:
            _assets = body.get('assets', {})
            body['assets'] = {}

            if not len(_assets.keys()):
                return

        _resources = []

        for asset_key, asset_body in _assets.items():

            _url = asset_body.get('href')

            _asset = {
                'title': asset_body.get('title'),
                'type': asset_body.get('type'),
                'roles': asset_body.get('roles'),
                'description': '',
                'role_name': asset_key
            }

            _name = _asset.get('title')
            _mimetype = _asset.get('type')
            # if _url:
            #     # if there is an href in the asset, we remove it from the json so it can be consistentely
            #     # be managed using the resource field "url"
            #     _asset[_asset_role].pop('href')

            
            _new_resource_dict = {
                _jsonschema_c.SCHEMA_OPT_KEY: json.dumps(opt),
                _jsonschema_c.SCHEMA_BODY_KEY: json.dumps(_asset),
                _jsonschema_c.SCHEMA_TYPE_KEY: _c.TYPE_STAC_RESOURCE,
                'url': _url,
                'name': _name,
                'mimetype': _mimetype
            }

            _resources.append(_new_resource_dict)
    
        data.update({'resources': _resources})

    def _extract_json_resources(self, data, errors, context):
        '''
        This methods extract the resources from the body of the stac-item (which are in a domain-specific position)
        and stores them in the "resources" field of the data, so that they can be processed later by the
        resource_extractor validator
        '''

        body = _t.get_context_body(context)
        
        _dict = {
            'name': body.get('title'),
        } 

        mimetype = body.get('type')
        if mimetype:
            _dict['mimetype'] = mimetype
        
        data.update(_dict)


class CatalogExtractor(StacExtractor):  
        

    def _extract_json_body(self, data, errors, context):
        
        body = _t.get_context_body(context)

        _dict = {
            'title': body.get('title'),
            'notes': body.get('description'),
            'license_id': body.get('license'),
            'version': body.get('stac_version')
        }

        data.update(_dict)

class CollectionExtractor(StacExtractor):

    def _extract_json_body(self, data, errors, context):
        
        body = _t.get_context_body(context)

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


    # def _extract_json_links(self, data, errors, context):

    #     body = _t.get_context_body(context)

    #     links = body.get('links')

    #     relevant = ['item'] # items should be feature

    #     for link in links:
    #         if link.get('rel') in relevant:

    #             data_dict = {
    #                 "from_xml": "False",
    #                 "import": "import",
    #                 "jsonschema_type": "stac",
    #                 "owner_org": data.get('owner_org'), # we set the same org of the parent
    #                 "package_update":"False",
    #                 "url": link.get('href')
    #             }

    #             importer(context, data_dict)
