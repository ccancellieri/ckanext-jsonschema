import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.jsonschema.interfaces as _i
import ckanext.jsonschema.logic.get as _g
from ckanext.jsonschema.stac import constants as _c
from ckanext.jsonschema.stac.extractor import ItemExtractor, CatalaogExtractor, CollectionExtractor, extract_id

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


    def supported_output_types(self, dataset_type, opt, version):
        if dataset_type == _c.TYPE_STAC:
            return [_c.TYPE_STAC]

    def dump_to_output(self, body, dataset_type, opt, version, data, output_format, context):
        pkg = _g.get_pkg(self.extract_id(body, dataset_type))
        if pkg:
            try:
                if dataset_type == _c.TYPE_STAC:
                    pass
                raise Exception(('Unsupported requested format {}').format(dataset_type))
            except Exception as e:
                if e:
                    message = ('Error on: {} line: {} Message:{}').format(e.get('name', ''), e.get('lineno', ''), e.get('message', ''))
                    log.error(message)

    def supported_resource_types(self, dataset_type, opt, version):
        if version != _c.SCHEMA_VERSION:
            log.warn(("Version: '{}' is not supported by this plugin ({})").format(version, __name__))
            return []
        if dataset_type == _c.TYPE_STAC:
            return _c.SUPPORTED_STAC_RESOURCE_FORMATS
        return []

    def supported_dataset_types(self, opt, version):
        if version != _c.SCHEMA_VERSION:
            return []
        return _c.SUPPORTED_DATASET_FORMATS

    def supported_input_types(self, opt, version):
        if version != _c.SCHEMA_VERSION:
            return []
        return _c.SUPPORTED_INPUT_FORMATS 


    def extract_from_json(self, body, type, opt, version, data, errors, context):

        _type = body.get('type')
        extractor = None

        if _type == _c.TYPE_STAC_ITEM:
            extractor = ItemExtractor()
            
        elif _type == _c.TYPE_STAC_CATALOG:
            extractor = CatalaogExtractor()

        elif _type == _c.TYPE_STAC_COLLECTION:
            extractor = CollectionExtractor()

        if extractor:
            extractor.extract_from_json(body, type, opt, version, data, errors, context)

        return (body, type, opt, version, data)
