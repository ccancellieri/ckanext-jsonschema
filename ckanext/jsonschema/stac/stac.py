import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.jsonschema.interfaces as _i
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.logic.get as _g
from ckanext.jsonschema.stac import constants as _c
from ckanext.jsonschema.stac.extractor import ItemExtractor, CatalogExtractor, CollectionExtractor, extract_id

log = logging.getLogger(__name__)


input_types = {
    _c.TYPE_STAC: ""
}

input_extractors = {
    _c.TYPE_STAC_ITEM: ItemExtractor().extract_from_json,
    _c.TYPE_STAC_CATALOG: CatalogExtractor().extract_from_json,
    _c.TYPE_STAC_COLLECTION: CollectionExtractor().extract_from_json
}

supported_types = {
    _c.TYPE_STAC: ""
}

supported_extractors = {
    _c.TYPE_STAC_ITEM: ItemExtractor().extract_from_json,
    _c.TYPE_STAC_CATALOG: CatalogExtractor().extract_from_json,
    _c.TYPE_STAC_COLLECTION: CollectionExtractor().extract_from_json
}

supported_resource_types = {
    _c.TYPE_STAC_RESOURCE: ItemExtractor()._extract_json_resources,
}

def dump_to_output(data, errors, context, output_format):

    body = _t.get_context_body(context)
    pkg = _t.get(body.get('id'))

    if pkg:
        try:
            pass
            #raise Exception(('Unsupported requested format {}').format(dataset_type))
        except Exception as e:
            if e:
                message = ('Error on: {} line: {} Message:{}').format(e.get('name', ''), e.get('lineno', ''), e.get('message', ''))
                log.error(message)


output_types = {
    _c.TYPE_STAC: dump_to_output
}

class JsonSchemaStac(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(_i.IBinder, inherit=True)

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'stac')

    def package_types(self):
        # We want a generic type "stac" in the interface
        # We will discriminate a more specific type later based on the data
        return [_c.TYPE_STAC]

    def extract_id(self, body, dataset_type, opt, verion, errors, context):
        return extract_id(dataset_type, body)

    def get_input_types(self):
        return input_types.keys()

    def get_supported_types(self):
        return supported_types.keys()

    def get_supported_resource_types(self):
        return supported_resource_types.keys()
    
    def get_input_extractor(self, package_type, context):

        body = _t.get_context_body(context)
        stac_type = body.get('type')

        extractor_for_type = input_extractors.get(stac_type)

        if extractor_for_type:
            return extractor_for_type
        else:
            raise KeyError('Extractor not defined for package with type {}, resolved in {}'.format(package_type, stac_type))
                

    def get_package_extractor(self, package_type, context):
        
        body = _t.get_context_body(context)
        stac_type = body.get('type')

        extractor_for_type = supported_extractors.get(stac_type)

        if extractor_for_type:
            return extractor_for_type
        else:
            raise KeyError('Extractor not defined for package with type {}, resolved in {}'.format(package_type, stac_type))

    def get_resource_extractor(self, package_type, resource_type, context):

        extractor_for_type = supported_resource_types.get(resource_type)

        if extractor_for_type:
            return extractor_for_type
        else:
            raise KeyError('Extractor not defined for resource with type {}'.format(resource_type))