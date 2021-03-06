import datetime

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
import ckanext.jsonschema.tools as _t
from ckanext.jsonschema.iso19139 import extractor, extractor_iso19139, tools as _it
from ckanext.jsonschema.iso19139.constants import (
    TYPE_ISO, TYPE_ISO19139, TYPE_ISO_RESOURCE_CITED_RESPONSIBLE_PARTY,
    TYPE_ISO_RESOURCE_DISTRIBUTOR, TYPE_ISO_RESOURCE_GRAPHIC_OVERVIEW,
    TYPE_ISO_RESOURCE_MAINTAINER, TYPE_ISO_RESOURCE_METADATA_CONTACT,
    TYPE_ISO_RESOURCE_ONLINE_RESOURCE, TYPE_ISO_RESOURCE_RESOURCE_CONTACT)

log = logging.getLogger(__name__)


#############################################

import json

import ckan.lib.navl.dictization_functions as df

config = toolkit.config


input_types = {
    TYPE_ISO19139: extractor_iso19139._extract_iso
}

supported_types = {
    TYPE_ISO: extractor._extract_from_iso,
}

supported_resource_types = {
    # TYPE_ISO_RESOURCE_ONLINE_RESOURCE,
    # TYPE_ISO_RESOURCE_DATASET,
    TYPE_ISO_RESOURCE_DISTRIBUTOR: extractor._extract_iso_resource_responsible,
    TYPE_ISO_RESOURCE_ONLINE_RESOURCE: extractor._extract_iso_online_resource,
    TYPE_ISO_RESOURCE_GRAPHIC_OVERVIEW: extractor._extract_iso_graphic_overview,
    TYPE_ISO_RESOURCE_METADATA_CONTACT: extractor._extract_iso_resource_responsible,
    TYPE_ISO_RESOURCE_RESOURCE_CONTACT: extractor._extract_iso_resource_responsible,
    TYPE_ISO_RESOURCE_MAINTAINER: extractor._extract_iso_resource_responsible,
    TYPE_ISO_RESOURCE_CITED_RESPONSIBLE_PARTY: extractor._extract_iso_resource_responsible
}


def clone(source_pkg, package_dict, errors, context):
   
    _type = _t.get_package_type(source_pkg)
    body = _t.get_package_body(source_pkg)

    now = datetime.datetime.now().isoformat()

    opt = {
        'cloned' : True,
        'source_url': source_pkg.get('url'),
        'cloned_on': str(now)
    }

    # change the ID
    title_idx = ('dataIdentification','citation','title',)
    title = _t.get_nested(body, title_idx)
    if not title:
        title = body.get('fileIdentifier','')

    _t.set_nested(body, title_idx, 'Cloned {} {}'.format(title, now))

    body['fileIdentifier'] = ''
    
    package_dict.update({
        _c.SCHEMA_BODY_KEY: body,
        _c.SCHEMA_TYPE_KEY : _type,
        _c.SCHEMA_OPT_KEY : opt,
    })

clonable_package_types = {
    TYPE_ISO: clone,
}

clonable_resources_types = {
    TYPE_ISO_RESOURCE_DISTRIBUTOR: _i.default_cloner,
    TYPE_ISO_RESOURCE_METADATA_CONTACT: _i.default_cloner,
    TYPE_ISO_RESOURCE_RESOURCE_CONTACT: _i.default_cloner,
    TYPE_ISO_RESOURCE_MAINTAINER: _i.default_cloner,
    TYPE_ISO_RESOURCE_CITED_RESPONSIBLE_PARTY: _i.default_cloner
}

def dump_to_output(data, errors, context, output_format):
    import ckan.lib.base as base

    body = _t.get_package_body(data)
    pkg = _t.get(body.get('fileIdentifier'))
    
    # TODO why not use data as model is get_pkg a good model??

    if pkg:
        try:
            ######################
            # TODO so we have to use format and mimetype
            # format 'can' be 1:1 with dataset_type
            ##########

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

output_types = {
    TYPE_ISO: dump_to_output
}


class JsonschemaIso(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(_i.IBinder, inherit = True)


    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'ckanext-jsonschema')

    
    def get_input_types(self):
        return input_types.keys()

    def get_supported_types(self):
        return supported_types.keys()

    def get_supported_resource_types(self):
        return supported_resource_types.keys()

    def get_clonable_resource_types(self):
        return clonable_resources_types.keys()

    # TODO
    def get_input_extractor(self, package_type, package_dict, context):
        
        extractor_for_type = input_types.get(package_type)
        
        if extractor_for_type:
            return extractor_for_type
        else:
            raise KeyError('Input extractor not defined for package with type {}'.format(package_type))


    def get_package_extractor(self, package_type, package_dict, context):
        
        extractor_for_type = supported_types.get(package_type)

        if extractor_for_type:
            return extractor_for_type
        else:
            raise KeyError('Extractor not defined for package with type {}'.format(package_type))


    def get_resource_extractor(self, package_type, resource_type, context):

        extractor_for_type = supported_resource_types.get(resource_type)

        if extractor_for_type:
            return extractor_for_type
        else:
            raise KeyError('Extractor not defined for package with type {}'.format(resource_type))

    def get_package_cloner(self, package_type):
        return clonable_package_types.get(package_type)


    def get_resource_cloner(self, package_type, resource_type):            
        return clonable_resources_types.get(resource_type)


    def get_dump_to_output(self, package_type):
        return output_types.get(package_type)

    # IBinder
    def extract_id(self, data, errors, context):
        
        dataset_type = _t.get_package_type(data)
        body = _t.get_package_body(data)

        if dataset_type == TYPE_ISO:
            return extractor._extract_id(body)

        elif dataset_type == TYPE_ISO19139:
            return extractor_iso19139._extract_id(body)