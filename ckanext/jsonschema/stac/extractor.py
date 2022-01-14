import json
import uuid

import ckan.lib.helpers as h
import ckan.lib.munge as munge
import ckan.model
import ckanext.jsonschema.constants as _jsonschema_c
import ckanext.jsonschema.validators as _v
import pylons
from ckanext.jsonschema.logic.actions import importer
from ckanext.jsonschema.stac import constants as _c


def extract_id(dataset_type, body):
        if dataset_type == _c.TYPE_STAC:
            return body.get('id')

class StacExtractor():

    def extract_from_json(self, body, type, opt, version, data, errors, context):
        
        try:
            self._extract_json_name(body, type, opt, version, data, errors, context)
            self._extract_json_body(body, type, opt, version, data, errors, context)
            self._extract_json_other(body, type, opt, version, data, errors, context)

        except Exception as e:
            _v.stop_with_error(('Error decoding metadata identification: {}').format(str(e)), 'metadata identifier', errors)

        return (body, type, opt, version, data)


    def _extract_json_name(self, body, type, opt, version, data, errors, context):
        
        name = self._extract_id(type, body)
        
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

    def _extract_json_body(self, body, type, opt, version, data, errors, context):
        raise NotImplementedError("Please Implement this method ")

    def _extract_json_other(self, body, type, opt, version, data, errors, context):
        """
        This function can be used to extract specific objects respect to the type of the extractor
        For example, ItemExtractor can extract resources and CollectionExtractor can extract links
        """
        pass


class ItemExtractor(StacExtractor):

    def _extract_json_body(self, body, type, opt, version, data, errors, context):
        
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

    def _extract_json_other(self, body, type, opt, version, data, errors, context):
        return self._extract_json_resources(body, type, opt, version, data, errors, context)

    def _extract_json_resources(self, body, type, opt, version, data, errors, context):
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


class CatalaogExtractor(StacExtractor):  
        

    def _extract_json_body(self, body, type, opt, version, data, errors, context):
        
        _dict = {
            'title': body.get('title'),
            'notes': body.get('description'),
            'license_id': body.get('license'),
            'version': body.get('stac_version')
        }

        data.update(_dict)

class CollectionExtractor(StacExtractor):

    def _extract_json_body(self, body, type, opt, version, data, errors, context):
        
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


    def _extract_json_other(self, body, type, opt, version, data, errors, context):
        pass
        #return self._extract_json_links(body, type, opt, version, data, errors, context)

    def _extract_json_links(self, body, type, opt, version, data, errors, context):

        links = body.get('links')

        relevant = ['item'] # items should be feature

        for link in links:
            if link.get('rel') in relevant:

                data_dict = {
                    "from_xml": "False",
                    "import": "import",
                    "jsonschema_type": "stac",
                    "owner_org": data.get('owner_org'), # we set the same org of the parent
                    "package_update":"False",
                    "url": link.get('href')
                }

                importer(context, data_dict)
