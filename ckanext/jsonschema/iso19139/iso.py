import ckan.plugins as p
import ckan.plugins.toolkit as toolkit

not_empty = toolkit.get_validator('not_empty')
is_boolean = toolkit.get_validator('boolean_validator')

import ckan.lib.navl.dictization_functions as df

missing = df.missing
StopOnError = df.StopOnError
Invalid = df.Invalid

import logging

import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.interfaces as _i
import ckanext.jsonschema.logic.get as _g
import ckanext.jsonschema.tools as _t
from ckanext.jsonschema.iso19139 import extractor
from ckanext.jsonschema.iso19139 import extractor_iso19139
from ckanext.jsonschema.iso19139.constants import (
    TYPE_ISO, TYPE_ISO19139, SUPPORTED_DATASET_FORMATS, SUPPORTED_ISO_RESOURCE_FORMATS,
    TYPE_ISO_RESOURCE_CITED_RESPONSIBLE_PARTY, TYPE_ISO_RESOURCE_DISTRIBUTOR, 
    TYPE_ISO_RESOURCE_GRAPHIC_OVERVIEW, TYPE_ISO_RESOURCE_MAINTAINER, 
    TYPE_ISO_RESOURCE_METADATA_CONTACT, TYPE_ISO_RESOURCE_ONLINE_RESOURCE,
    TYPE_ISO_RESOURCE_RESOURCE_CONTACT,
    SUPPORTED_ISO_INPUT_TYPES
    )

log = logging.getLogger(__name__)


#############################################

import json

import ckan.lib.navl.dictization_functions as df

config = toolkit.config

class JsonschemaIso(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(_i.IBinder, inherit = True)

    # IConfigurer
    def update_config(self, config_):
        pass
        #TODO

        
    # IBinder
    def extract_id(self, body, dataset_type, opt, version, errors, context):
        if dataset_type == TYPE_ISO:
            return extractor._extract_id(body)

        elif dataset_type == TYPE_ISO19139:
            return extractor_iso19139._extract_id(body)
        
    def supported_input_types(self, opt, version):
        return SUPPORTED_ISO_INPUT_TYPES


    def supported_resource_types(self, dataset_type, opt=_c.SCHEMA_OPT, version=_c.SCHEMA_VERSION):
        if version != _c.SCHEMA_VERSION:
            log.warn('Version: \'{}\' is not supported by this plugin ({})'.format(version, __name__))
            # when version is not the default one we don't touch
            return []
        # TODO MAPPING
        if dataset_type == TYPE_ISO:
            return SUPPORTED_ISO_RESOURCE_FORMATS
        return []
        

    def supported_dataset_types(self, opt=_c.SCHEMA_OPT, version=_c.SCHEMA_VERSION):
        if version != _c.SCHEMA_VERSION:
            # when version is not the default one we don't touch
            return []
        return SUPPORTED_DATASET_FORMATS


    def supported_output_types(self, dataset_type, opt, version):
        if dataset_type == TYPE_ISO:
            return ['iso']
        return []


    def before_extractor(self, body, type, opt, version, data, errors, context):
        
        if type == TYPE_ISO19139:
            return extractor_iso19139._extract_iso(body, opt, version, data, errors, context)

        return body, type, opt, version, data


    def extract_from_json(self, body, type, opt, version, data, errors, context):
        
        if type == TYPE_ISO:
            return extractor._extract_from_iso(body, type, opt, version, data, errors, context)

        # TYPE_ISO_RESOURCE_ONLINE_RESOURCE,
        # TYPE_ISO_RESOURCE_DATASET,

        elif type == TYPE_ISO_RESOURCE_DISTRIBUTOR:
            return extractor._extract_iso_resource_responsible(body, type, opt, version, data, errors, context)
            
        elif type == TYPE_ISO_RESOURCE_ONLINE_RESOURCE:
            return extractor._extract_iso_online_resource(body, type, opt, version, data, errors, context)
            
        elif type == TYPE_ISO_RESOURCE_GRAPHIC_OVERVIEW:
            return extractor._extract_iso_graphic_overview(body, type, opt, version, data, errors, context)
            
        elif type == TYPE_ISO_RESOURCE_METADATA_CONTACT:
            return extractor._extract_iso_resource_responsible(body, type, opt, version, data, errors, context)
        
        elif type == TYPE_ISO_RESOURCE_RESOURCE_CONTACT:
            return extractor._extract_iso_resource_responsible(body, type, opt, version, data, errors, context)
            
        elif type == TYPE_ISO_RESOURCE_MAINTAINER:
            return extractor._extract_iso_resource_responsible(body, type, opt, version, data, errors, context)
                        
        elif type == TYPE_ISO_RESOURCE_CITED_RESPONSIBLE_PARTY:
            return extractor._extract_iso_resource_responsible(body, type, opt, version, data, errors, context)
            
        return body, type, opt, version, data


    def dump_to_output(self, body, dataset_type, opt, version, data, output_format, context):
        import ckan.lib.base as base

        pkg = _g.get_pkg(body.get('fileIdentifier'))
        # TODO why not use data as model is get_pkg a good model??

        if pkg:
            try:
                ######################
                # TODO so we have to use format and mimetype
                # format 'can' be 1:1 with dataset_type
                ##########

                if dataset_type == 'iso':
                    if output_format == 'xml':
                        return base.render('iso/iso19139.xml', extra_vars={'metadata': body, 'pkg': pkg})
                    elif output_format == 'json':
                        return json.dumps(data)
                    elif output_format == 'html':
                        return base.render('iso/fullview.html', extra_vars={'dataset': pkg})
                        
                # if dataset_type == 'iso19139' and output_format == 'xml':
                #     return base.render('iso/iso19139.xml', extra_vars={'metadata': body, 'pkg': pkg})
                
                raise Exception('Unsupported requested format {}'.format(dataset_type))
            except Exception as e:
                try:
                    message = 'Error on: {} line: {} Message:{}'.format(e.name, e.lineno, e.message)
                    log.error(message)
                except:
                    log.error('Exception: {}'.format(type(e)))
                    log.error(str(e))
                # raise e
                # raise e
