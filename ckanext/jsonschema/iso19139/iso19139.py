from sqlalchemy.sql.expression import true

import ckan.lib.helpers as h
import ckan.plugins.toolkit as toolkit

_get_or_bust= toolkit.get_or_bust
_ = toolkit._
import ckan.plugins as p

# import ckan.logic.validators as v

not_empty = toolkit.get_validator('not_empty')
#ignore_missing = p.toolkit.get_validator('ignore_missing')
#ignore_empty = p.toolkit.get_validator('ignore_empty')
is_boolean = toolkit.get_validator('boolean_validator')
# https://docs.ckan.org/en/2.8/extensions/validators.html#ckan.logic.validators.json_object
# NOT FOUND import ckan.logic.validators.json_object
#json_object = p.toolkit.get_validator('json_object')
# isodate

import ckan.lib.navl.dictization_functions as df

missing = df.missing
StopOnError = df.StopOnError
Invalid = df.Invalid

import ckanext.jsonschema.validators as _v
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.interfaces as _i

import logging
log = logging.getLogger(__name__)


#############################################

import jsonschema
from jsonschema import validate,RefResolver,Draft4Validator,Draft7Validator
import json
import ckan.model as model

TYPE_ONLINE_RESOURCE='online-resource'
TYPE_ISO19139='iso19139'

SUPPORTED_DATASET_FORMATS = [TYPE_ISO19139]
SUPPORTED_RESOURCE_FORMATS = [TYPE_ONLINE_RESOURCE]

class JsonschemaIso19139(p.SingletonPlugin):
    p.implements(_i.IBinder, inherit=True)

        # namespaces = {u'http://www.opengis.net/gml/3.2': u'gml', u'http://www.isotc211.org/2005/srv': u'srv', u'http://www.isotc211.org/2005/gts': u'gts', u'http://www.isotc211.org/2005/gmx': u'gmx', u'http://www.isotc211.org/2005/gmd': u'gmd', u'http://www.isotc211.org/2005/gsr': u'gsr', u'http://www.w3.org/2001/XMLSchema-instance': u'xsi', u'http://www.isotc211.org/2005/gco': u'gco', u'http://www.isotc211.org/2005/gmi': u'gmi', u'http://www.w3.org/1999/xlink': u'xlink'}
        # # TODO DEBUG
        # import ckanext.jsonschema.utils as _u
        # import os
        # j = _u.xml_to_json_from_file(os.path.join(_c.PATH_TEMPLATE,'test_iso.xml'))
        # import json
        # _j=json.loads(j)
        # _namespaces=_j['http://www.isotc211.org/2005/gmd:MD_Metadata']['@xmlns']
        # namespaces = dict((v,k) for k,v in _namespaces.iteritems())
        # _u.json_to_xml()
        # _u.xml_to_json_from_file(os.path.join(_c.PATH_TEMPLATE,'test_iso.xml'), True, namespaces)

    def supported_resource_types(self, dataset_type, opt=_c.SCHEMA_OPT, version=_c.SCHEMA_VERSION):
        if version != _c.SCHEMA_VERSION:
            # when version is not the default one we don't touch
            return []

        if dataset_type in SUPPORTED_DATASET_FORMATS:
            #TODO should be a dic binding set of resources to dataset types 
            return SUPPORTED_RESOURCE_FORMATS

        return []

    def supported_dataset_types(self, opt, version):
        if version != _c.SCHEMA_VERSION:
            # when version is not the default one we don't touch
            return []

        return SUPPORTED_DATASET_FORMATS

    def extract_from_json(self, body, type, opt, version, key, data, errors, context):
        # TODO which type schema or dataset?
        
        if key==('name',):
            extract_name(body, opt, type, version, key, data, errors, context)
        else:
            _extract_iso(body, opt, type, version, key, data, errors, context)
        # if type == TYPE_ONLINE_RESOURCE:
        #     _create_online_resources(body, opt, type, version, key, data, errors, context)


import ckan.lib.navl.dictization_functions as df

def extract_name(body, opt, type, version, key, data, errors, context):

    _data = df.unflatten(data)

    # name:
    #<gmd:MD_Metadata 
    #<gmd:fileIdentifier>
    #<gco:CharacterString>c26de669-90f9-43a1-ae4d-6b1b9660f5e0</gco:CharacterString>
    # TODO generate if still none...

    name = body.get("gmd:MD_Metadata", {})\
                            .get('gmd:fileIdentifier', {})\
                                .get('gco:CharacterString')
    name = name or _data.get('name') #TODO error if null...

    if not name:
        _v.stop_with_error('Unable to obtain {}'.format(key), key, errors)
        
    _dict = {
        'name': name,
        'url': h.url_for(controller = 'package', action = 'read', id = name, _external = True),
    }
    data.update(df.flatten_dict(_dict))

def _extract_iso(body, opt, type, version, key, data, errors, context):

    # let's play with normal dict
    
    _data = df.unflatten(data)

    identification = body.get("gmd:MD_Metadata", {})\
                            .get('gmd:identificationInfo',{})\
                                .get('gmd:MD_DataIdentification')

    if not identification:
        _v.stop_with_error('Unable to find identification info', key, errors)
            
    citation = identification.get('gmd:citation', {})\
                                .get('gmd:CI_Citation')

    if not citation:
        _v.stop_with_error('Unable to find citation info', key, errors)

    # title:
    # <gmd:identificationInfo xmlns:geonet="http://www.fao.org/geonetwork">
    # <gmd:MD_DataIdentification>
    # <gmd:citation>
    # <gmd:CI_Citation>
    # <gmd:title>
    # <gco:CharacterString>
    title = _data.get('title','')
    _title = citation.get('gmd:title', {}).get('gco:CharacterString')\
            or\
            citation.get('gmd:alternateTitle', {}).get('gco:CharacterString')
    title = title or _title

    # <gmd:abstract>
    # <gco:CharacterString>
    abstract = identification.get('gmd:abstract', {}).get('gco:CharacterString')
        
    # description / notes / abstract
    notes = abstract or _data.get('notes')

    # <gmd:purpose>
    # <gco:CharacterString>
    
    # <gmd:credit>
    # <gco:CharacterString>


# name = body.get("gmd:MD_Metadata", {})\
#                         .get('gmd:fileIdentifier', {})\
#                             .get('gco:CharacterString')
# name = name or _data.get('name') #TODO error if null...
    # TODO generate if still none

    # version
    # <gmd:MD_Metadata
    # <gmd:metadataStandardVersion xmlns:geonet="http://www.fao.org/geonetwork">
    # <gco:CharacterString>1.0</gco:CharacterString>

    # type
    # <gmd:MD_Metadata
    # <gmd:metadataStandardName xmlns:geonet="http://www.fao.org/geonetwork">
    # <gco:CharacterString>ISO 19115:2003/19139</gco:CharacterString>
# body.get("gmd:MD_Metadata", {}).get('gmd:distributionInfo', {}).get('gmd:MD_Distribution', {})
    transfer_options = body.get("gmd:MD_Metadata", {})\
            .get('gmd:distributionInfo', {})\
                .get('gmd:MD_Distribution', {})\
                    .get('gmd:transferOptions')

    if transfer_options:
        _transfer_options = transfer_options
        if not isinstance(transfer_options, list):
            _transfer_options = [ transfer_options ]
        for options in _transfer_options:
            #"Geographic areas"
            # if not options or not isinstance(options, dict):
            #     continue
            transfer_opts = options.get('gmd:MD_DigitalTransferOptions', {})
            if not transfer_opts:
                continue
                #TODO: LOGS
                #_v.stop_with_error('Unable to find transfer options', key, errors)
            
            # transfer_opts.get('gmd:unitsOfDistribution', {}).get('gco:CharacterString') 
            # transfer_opts.get('gmd:transferSize', {}).get('gco:Real') 
            
            online = transfer_opts.get('gmd:onLine', [])
            if isinstance(online, list):
                for idx, online_resource in enumerate(list(online)):
                    pop_online(online_resource, opt, type, version, key, data, errors, context)
                    online.remove(online_resource)
            else:
                pop_online(online, opt, type, version, key, data, errors, context)
                transfer_opts.pop('gmd:onLine')

            
                
    _dict = {
        'title': title,
        'notes': notes,
        # _c.SCHEMA_BODY_KEY: json.dumps(body),
        # _c.SCHEMA_TYPE_KEY: type,
        # _c.SCHEMA_OPT_KEY: json.dumps(opt),
        # _c.SCHEMA_VERSION_KEY: json.dumps(_c.SCHEMA_VERSION),
    }

    # context['defer_commit']=True# TODO #########################################CHECKME WHY??
    # let's return flatten dict as per specifications
    data.update(df.flatten_dict(_dict))

def pop_online(online_resource, opt, type, version, key, data, errors, context):
    if isinstance(online_resource, list):
            for resource in online_resource:
                pop_online_resource(resource, opt, type, version, key, data, errors, context)
    else:
        pop_online_resource(online_resource, opt, type, version, key, data, errors, context)

def pop_online_resource(resource, opt, type, version, key, data, errors, context):
    r = resource.pop('gmd:CI_OnlineResource', None)
    if r:
        extract_online_resource(r, opt, TYPE_ONLINE_RESOURCE, version, key, data, errors, context)
    else:
        _v.stop_with_error('Unable to extract online resource: '.format(str(resource)), key, errors)
    
def extract_online_resource(body, opt, type, version, key, data, errors, context):
    
    # let's play with normal dict
    _data = df.unflatten(data)

    # we assume:
    # - body is an gmd:CI_OnlineResource

    # TODO recursive validation triggered by resource_create action ?
    new_resource= {
        # TODO otherwise do all here
        'title': body.get('gmd:name', {}).get('gco:CharacterString', ''),
        'description': body.get('gmd:description', {}).get('gco:CharacterString', ''),
        'url': body.get('gmd:linkage', {}).get('gmd:URL', ''),
        # _c.SCHEMA_VERSION_KEY: json.dumps(version),
        # _c.SCHEMA_BODY_KEY: json.dumps(body),
        # _c.SCHEMA_TYPE_KEY: type,
    }
    protocol = body.get('gmd:protocol', {}).get('gco:CharacterString')
    new_resource.update({
        'format': _get_type_from(protocol, new_resource.get('url')) or ''
    })

    resources = _data.get('resources', [])
    resources.append(new_resource)
    data.update(df.flatten_dict({'resources': resources}))

    # TODO remove from body what is not managed by json
    


def default_lon_e(key, data, errors, context):
    '''
    Validator providing default values 
    '''
    if not data[key]:
        data[key]=180
        return
    try:
        if float(data[key])>180:
            data[key]=180
    except ValueError:
        data[key]=180

def default_lon_w(key, data, errors, context):
    '''
    Validator providing default values 
    '''
    if not data[key]:
        data[key]=-180
        return
    try:
        if float(data[key])<-180:
            data[key]=-180
    except ValueError:
        data[key]=-180

def default_lat_n(key, data, errors, context):
    '''
    Validator providing default values 
    '''
    if not data[key]:
        data[key]=90
        return
    try:
        if float(data[key])>90:
            data[key]=90
    except ValueError:
        data[key]=90

def default_lat_s(key, data, errors, context):
    '''
    Validator providing default values 
    '''
    if not data[key]:
        data[key]=-90
        return
    try:
        if float(data[key])<-90:
            data[key]=-90
    except ValueError:
        data[key]=-90