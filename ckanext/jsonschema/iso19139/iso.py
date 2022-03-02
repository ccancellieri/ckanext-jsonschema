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
    TYPE_ISO, TYPE_ISO19139,
    TYPE_ISO_RESOURCE_CITED_RESPONSIBLE_PARTY, TYPE_ISO_RESOURCE_DISTRIBUTOR, 
    TYPE_ISO_RESOURCE_GRAPHIC_OVERVIEW, TYPE_ISO_RESOURCE_MAINTAINER, 
    TYPE_ISO_RESOURCE_METADATA_CONTACT, TYPE_ISO_RESOURCE_ONLINE_RESOURCE,
    TYPE_ISO_RESOURCE_RESOURCE_CONTACT,
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

    # TODO
    def get_input_extractor(self, package_type, context):
        
        extractors = {
            TYPE_ISO19139: extractor_iso19139._extract_iso
        }

        extractor_for_type = extractors.get(package_type)
        
        if extractor_for_type:
            return extractor_for_type
        else:
            raise KeyError('Input extractor not defined for package with type {}'.format(package_type))


    def get_package_extractor(self, package_type, context):
        
        extractors = {
            TYPE_ISO: extractor._extract_from_iso,
        }   

        extractor_for_type = extractors.get(package_type)

        if extractor_for_type:
            return extractor_for_type
        else:
            raise KeyError('Extractor not defined for package with type {}'.format(package_type))


    def get_resource_extractor(self, package_type, resource_type, context):

        extractors = {
            # TYPE_ISO_RESOURCE_ONLINE_RESOURCE,
            # TYPE_ISO_RESOURCE_DATASET,
            TYPE_ISO_RESOURCE_DISTRIBUTOR: extractor._extract_iso_resource_responsible,
            TYPE_ISO_RESOURCE_ONLINE_RESOURCE: extractor._extract_iso_online_resource,
            TYPE_ISO_RESOURCE_GRAPHIC_OVERVIEW: extractor._extract_iso_graphic_overview,
            TYPE_ISO_RESOURCE_METADATA_CONTACT: extractor._extract_iso_resource_responsible,
            TYPE_ISO_RESOURCE_RESOURCE_CONTACT: extractor._extract_iso_resource_responsible,
            TYPE_ISO_RESOURCE_MAINTAINER: extractor._extract_iso_resource_responsible,
            TYPE_ISO_RESOURCE_CITED_RESPONSIBLE_PARTY: extractor._extract_iso_resource_responsible,
        }

        extractor_for_type = extractors.get(resource_type)

        if extractor_for_type:
            return extractor_for_type
        else:
            raise KeyError('Extractor not defined for package with type {}'.format(resource_type))

        
    # IBinder
    def extract_id(self, data, errors, context):
        
        dataset_type = _t.get_context_type(context)
        body = _t.get_context_body(context)

        if dataset_type == TYPE_ISO:
            return extractor._extract_id(body)

        elif dataset_type == TYPE_ISO19139:
            return extractor_iso19139._extract_id(body)
            

    def dump_to_output(self, data, errors, context, output_format):
        import ckan.lib.base as base

        body = _t.get_context_body(context)
        pkg = _t.get(body.get('fileIdentifier'))
        dataset_type = _t.get_context_type(context)
        
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
                
                raise Exception('Unsupported requested format {}'.format(output_format))
            except Exception as e:
                try:
                    if hasattr(e, 'name'):
                        message = 'Error on: {} line: {} Message:{}'.format(e.name, e.lineno, e.message)
                        log.error(message)
                    else:
                        raise
                except:
                    log.error('Exception: {}'.format(type(e)))
                    log.error(str(e))
                    raise
                # raise e

    def clone(self, package_dict, errors, context):
        body = _t.get_context_body(context)

        # reset the ID so that it is assigned by extract_from_json
        body['fileIdentifier'] = ''

        # filter resources

    def clone_resource(self, resource_dict, errors, context):
        pass