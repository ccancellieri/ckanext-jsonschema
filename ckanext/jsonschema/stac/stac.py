import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.jsonschema.interfaces as _i
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.logic.get as _g
from ckanext.jsonschema.stac import constants as _c
from ckanext.jsonschema.stac.extractor import ItemExtractor, CatalogExtractor, CollectionExtractor, extract_id

log = logging.getLogger(__name__)

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


    def dump_to_output(self, data, errors, context, output_format):

        body = _t.get_context_body(context)
        dataset_type = _t.get_context_type(context)


        pkg = _t.get(self.extract_id(body, dataset_type))
        if pkg:
            try:
                if dataset_type == _c.TYPE_STAC:
                    pass
                raise Exception(('Unsupported requested format {}').format(dataset_type))
            except Exception as e:
                if e:
                    message = ('Error on: {} line: {} Message:{}').format(e.get('name', ''), e.get('lineno', ''), e.get('message', ''))
                    log.error(message)


    def get_input_extractor(self, package_type, context):

        body = _t.get_context_body(context)
        stac_type = body.get('type')

        extractors = {
            _c.TYPE_STAC_ITEM: ItemExtractor().extract_from_json,
            _c.TYPE_STAC_CATALOG: CatalogExtractor().extract_from_json,
            _c.TYPE_STAC_COLLECTION: CollectionExtractor().extract_from_json
        }

        extractor_for_type = extractors.get(stac_type)

        if extractor_for_type:
            return extractor_for_type
        else:
            raise KeyError('Extractor not defined for package with type {}, resolved in {}'.format(package_type, stac_type))
                

    def get_package_extractor(self, package_type, context):
        
        body = _t.get_context_body(context)
        stac_type = body.get('type')

        extractors = {
            _c.TYPE_STAC_ITEM: ItemExtractor().extract_from_json,
            _c.TYPE_STAC_CATALOG: CatalogExtractor().extract_from_json,
            _c.TYPE_STAC_COLLECTION: CollectionExtractor().extract_from_json
        }

        extractor_for_type = extractors.get(stac_type)

        if extractor_for_type:
            return extractor_for_type
        else:
            raise KeyError('Extractor not defined for package with type {}, resolved in {}'.format(package_type, stac_type))

    def get_resource_extractor(self, package_type, resource_type, context):

        extractors = {
            _c.TYPE_STAC_RESOURCE: ItemExtractor()._extract_json_resources,
        }

        extractor_for_type = extractors.get(resource_type)

        if extractor_for_type:
            return extractor_for_type
        else:
            raise KeyError('Extractor not defined for resource with type {}'.format(resource_type))
        
