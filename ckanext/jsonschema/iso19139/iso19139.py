from sqlalchemy.sql.expression import true
from sqlalchemy.sql.sqltypes import ARRAY

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
from ckanext.jsonschema.iso19139.iso import TYPE_ISO, get_format

import logging
log = logging.getLogger(__name__)


import ckan.lib.navl.dictization_functions as df


#############################################

import json
import ckan.model as model

TYPE_ONLINE_RESOURCE='online-resource'
TYPE_ISO19139='iso19139'

SUPPORTED_DATASET_FORMATS = [TYPE_ISO19139]
SUPPORTED_RESOURCE_FORMATS = []

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


    def before_extractor(self, body, type, opt, version, data, errors, context):
            
        if type == TYPE_ISO19139:
            return _extract_iso(body, opt, version, data, errors, context)

        return body, type, opt, version, data
        # if type == TYPE_ONLINE_RESOURCE:
            # _extract_transfer_options(body, opt, type, version, data, errors, context)



# def append_nested(_dict, tuple, value = {}):
#     try:
#         d = _dict
#         for k in tuple[:-1]:
#             v = d.get(k)
#             if not v:
#                 d = d.setdefault(k,{})
#             elif isinstance(v, list):
#                 d = {}
#                 v.append(d)
#             elif isinstance(v, dict):
#                 d = d[k]

#         d.update({tuple[-1:][0]:value})
#     except:
#         return None
#     return _dict

def set_nested(dict, tuple, value):
    try:
        d = dict
        for k in tuple[:-1]:
            d = d.setdefault(k,{})
        d.update({tuple[-1:][0]:value})
    except:
        return None
    return dict

def pop_nested(dict, tuple):
    d = dict
    for k in tuple[:-1]:
        try:
            d = d[k]
        except:
            return
    return d.pop(tuple[-1:][0])

def get_nested(dict, tuple):
    d = dict
    for k in tuple[:-1]:
        try:
            d = d[k]
        except:
            return
    # return d.get(tuple[-1:])
    return d.get(tuple[-1:][0])

# https://github.com/jab/bidict/blob/0.18.x/bidict/__init__.py#L90
#from bidict import FrozenOrderedBidict, bidict, inverted 
# OVERWRITE
# OnDup, RAISE, DROP_OLD
# bidict, inverted, 
# class RelaxBidict(FrozenOrderedBidict):
    # __slots__ = ()
    # on_dup = OnDup(key=RAISE, val=DROP_OLD, kv=RAISE)
    # on_dup = OVERWRITE


def map_to(from_dict, map, to_dict):
    errors=[]
    for (source_path, dest_path) in map.items():
        value = get_nested(from_dict, source_path)
        if value and not set_nested(to_dict, dest_path, value):
            errors.append({source_path, dest_path})
    return errors

# def map_inverse(to_dict, map, from_dict):
#     errors=[]
#     for (k,v) in inverted(map):
#         if not set_nested(to_dict, v, get_nested(from_dict, k)):
#             errors.append({k,v})
#     return errors

def __identification_info(identification_info):
    _ret = []
    if not isinstance(identification_info, list):
            identification_info = [identification_info]
    for identification in identification_info:
        _identification = {}
        if identification.get('gmd:MD_DataIdentification'):
            
            identification_fields = {
                
                ## DATA IDENTIFICATION ( citation )
                ('gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:title','gco:CharacterString'):('citation','title',),
# TODO date [] "gmd:citation": { "gmd:CI_Citation": {"gmd:date": [
                ('gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:edition','gco:CharacterString'):('citation','edition',),
                ('gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:presentationForm','gmd:CI_PresentationFormCode','gmd:CI_PresentationFormCode',):('citation','presentationForm',),
                
# TODO presentationForm []
                ('gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:collectiveTitle','gco:CharacterString'):('citation','series','name'),
                ('gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:collectiveTitle','gco:CharacterString'):('citation','series','issueIdentification'),
                ('gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:collectiveTitle','gco:CharacterString'):('citation','series','page'),
                ('gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:collectiveTitle','gco:CharacterString'):('citation','series','otherCitationDetails'),
                ('gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:collectiveTitle','gco:CharacterString'):('citation','series','collectiveTitle'),
                ('gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:collectiveTitle','gco:CharacterString'):('citation','series','ISBN'),
                ('gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:collectiveTitle','gco:CharacterString'):('citation','series','ISSN'),
                
                ('gmd:MD_DataIdentification','gmd:purpose','gco:CharacterString'):('purpose',),

# TODO resourceConstraints []
# TODO extent

                ('gmd:MD_DataIdentification','gmd:characterSet','gmd:MD_CharacterSetCode','@codeListValue'):('characterSet',),
                ('gmd:MD_DataIdentification','gmd:supplementalInformation','gco:CharacterString'):('supplementalInformation',),

# aggregationInfo []

                ('gmd:MD_DataIdentification','gmd:resourceMaintenance','gmd:MD_MaintenanceInformation','gmd:maintenanceAndUpdateFrequency','gmd:MD_MaintenanceFrequencyCode','@codeListValue'):('resourceMaintenance','maintenanceAndUpdateFrequency',),
# TODO extract "gmd:resourceMaintenance": { "gmd:MD_MaintenanceInformation": { "gmd:contact": { "gmd:CI_ResponsibleParty":...
# TODO topicCategory []
# TODO extract graphicOverview
                ('gmd:MD_DataIdentification','gmd:status','gmd:MD_ProgressCode','@codeListValue'):('status',),
# TODO descriptiveKeywords []

# TODO spatialRepresentationType []
# ('gmd:spatialRepresentationType','gmd:language','gco:CharacterString'):('language',),

                ('gmd:MD_DataIdentification','gmd:language','gco:CharacterString'):('language',),

# TODO extract 'gmd:pointOfContact'

                ('gmd:MD_DataIdentification','gmd:abstract','gco:CharacterString'):('abstract',),
# TODO spatialResolution []
                

                # resourceMaintenance
                
                ## DATA IDENTIFICATION (CITATIONS)
                # TODO (''):('dataIdentification','citation','edition',),
                # TODO presentationForm
                # TODO series
                
                
                # ('gmd:MD_Metadata','gmd:identificationInfo','gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:status','gmd:MD_ProgressCode','"@codeListValue',):('status',)

                # ('gmd:MD_Metadata','gmd:identificationInfo','gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:alternateTitle','gco:CharacterString'):'alternateTitle'
            }
            # map body to ckan fields (_data)
            errors = map_to(identification, identification_fields, _identification)


            # date = get_nested(sri, ('gmd:MD_GridSpatialRepresentation','gmd:axisDimensionProperties',))
            # if not isinstance(axis_dimension_properties, list):
            #     axis_dimension_properties = [axis_dimension_properties]
            # for axis in axis_dimension_properties:
            #     _axis = {}
            #     axis_fields = {
            #         ('gmd:MD_Dimension','gmd:dimensionSize','gco:Integer',):('dimensionSize'),
            #         ('gmd:MD_Dimension','gmd:dimensionName','gmd:MD_DimensionNameTypeCode','@codeListValue',):('dimensionName'),
            #         ('gmd:MD_Dimension','gmd:resolution','gco:Boolean',):('transformationParameterAvailability',),
            #     }
            #     errors = map_to(axis, axis_fields, _axis)
            #     _sri['dimension'].append(_axis)
        else:
            continue

        _ret.append(_identification)
        
    return _ret

def __spatial_representation_info(spatial_representation_info):
    # spatial_representation_info = get_nested(body, ('gmd:MD_Metadata','gmd:spatialRepresentationInfo',))
    _ret = []
    if not isinstance(spatial_representation_info, list):
            spatial_representation_info = [spatial_representation_info]
    for sri in spatial_representation_info:
        _sri = {}
        if sri.get('gmd:MD_GridSpatialRepresentation'):
            # GRID
            grid_spatial_representation_info_fields = {
                
                ('gmd:MD_GridSpatialRepresentation','gmd:numberOfDimensions','gco:Integer',):('numberOfDimensions',),
                ('gmd:MD_GridSpatialRepresentation','gmd:transformationParameterAvailability','gco:Boolean',):('transformationParameterAvailability',),
                ('gmd:MD_GridSpatialRepresentation','gmd:cellGeometry','@codeListValue',):('cellGeometry',),
            }
            # map body to ckan fields (_data)
            errors = map_to(sri, grid_spatial_representation_info_fields, _sri)

            axis_dimension_properties = get_nested(sri, ('gmd:MD_GridSpatialRepresentation','gmd:axisDimensionProperties',))
            if not isinstance(axis_dimension_properties, list):
                axis_dimension_properties = [axis_dimension_properties]
            _dimensions = []
            _sri['dimension'] = _dimensions
            for axis in axis_dimension_properties:
                _axis = {}
                axis_fields = {
                    ('gmd:MD_Dimension','gmd:dimensionSize','gco:Integer',):('dimensionSize',),
                    ('gmd:MD_Dimension','gmd:dimensionName','gmd:MD_DimensionNameTypeCode','@codeListValue',):('dimensionName',),
                    ('gmd:MD_Dimension','gmd:resolution','gco:Boolean',):('transformationParameterAvailability',),
                }
                errors = map_to(axis, axis_fields, _axis)
                _dimensions.append(_axis)

        elif sri.get('gmd:MD_VectorSpatialRepresentation'):
            # VECTOR
            vector_spatial_representation_info_fields = {
                ('gmd:MD_VectorSpatialRepresentation','gmd:transformationParameterAvailability','gco:Boolean',):('transformationParameterAvailability',),
                ('gmd:MD_VectorSpatialRepresentation','gmd:cellGeometry','@codeListValue',):('cellGeometry',)
            }
            errors = map_to(sri, vector_spatial_representation_info_fields, _sri)

            geometric_objects = get_nested(sri, ('gmd:MD_VectorSpatialRepresentation','gmd:geometricObjects','gmd:MD_GeometricObjects',))
            if not isinstance(geometric_objects, list):
                geometric_objects = [geometric_objects]
            _geometric_object = []
            _sri['geometricObjects'] = _geometric_object
            for go in geometric_objects:
                _go = {}
                go_fields = {
                    ('gmd:geometricObjectCount','gco:Integer',) : ('geometricObjectCount',),
                    ('gmd:geometricObjectType','gmd:MD_GeometricObjectTypeCode','@codeListValue',) : ('geometricObjectType',),
                }
                errors = map_to(go, go_fields, _go)
                _geometric_object.append(_go)
        else:
            continue

        _ret.append(_sri)
        
    return _ret



# context = {
#         _c.SCHEMA_OPT_KEY : opt,
#         _c.SCHEMA_VERSION_KEY : version
#     }
# def _extract_iso(body, type, data, context):        
def _extract_iso(body, opt, version, data, errors, context):

    
    # DATA translation
    # root_fields = FrozenOrderedBidict({
    root_fields = {
        
        ('gmd:MD_Metadata','gmd:fileIdentifier','gco:CharacterString'):('fileIdentifier',),
        ('gmd:MD_Metadata','gmd:metadataStandardName','gco:CharacterString'):('metadataStandardName',), # TODO this could be an array
        ('gmd:MD_Metadata','gmd:characterSet','gmd:MD_CharacterSetCode','@codeListValue',):('characterSet',),
        ('gmd:MD_Metadata','gmd:identificationInfo','gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:language','gco:CharacterString',):('language',),
        ('gmd:MD_Metadata','gmd:metadataStandardVersion','gco:CharacterString'):('metadataStandardVersion',),
        ('gmd:MD_Metadata','gco:CharacterString'):('parentIdentifier',),
        
        ('gmd:MD_Metadata','gmd:referenceSystemInfo','gmd:MD_ReferenceSystem','gmd:RS_Identifier','gmd:code','gco:CharacterString'):('referenceSystemIdentifier',),
        
        # # see below spatial_representation_info()
        # ('gmd:MD_Metadata','gmd:spatialRepresentationInfo',):('spatialRepresentationInfo',)


        ('gmd:MD_Metadata','gmd:dataQualityInfo','gmd:DQ_DataQuality','gmd:lineage','gmd:LI_Lineage','gmd:statement','gco:CharacterString'):('dataQualityInfo','lineage','statement',),
        # TODO dataQualityInfo complete LI_Lineage gmd:source

        ## DATA IDENTIFICATION
    }
    _data = dict(data)
    _body = dict(body)
    _iso_profile = {}
    # map body to ckan fields (_data)
    errors = map_to(_body, root_fields, _iso_profile)
    
    if errors:
        # TODO map errors {key,error} to ckan errors 
        # _v.stop_with_error('Unable to map to iso', errors)
        log.error('unable to map')

    spatial_representation_info = get_nested(body, ('gmd:MD_Metadata','gmd:spatialRepresentationInfo',))
    if spatial_representation_info:
        _spatial_representation_info = __spatial_representation_info(spatial_representation_info)
        set_nested(_iso_profile, ('spatialRepresentationInfo',), _spatial_representation_info)

    identification_info = get_nested(body, ('gmd:MD_Metadata','gmd:identificationInfo',))
    if identification_info:
        _identification_info = __identification_info(identification_info)
        set_nested(_iso_profile, ('dataIdentification',), _identification_info)


    # ('gmd:MD_Metadata','gmd:distributionInfo','gmd:MD_Distribution','gmd:transferOptions',):('transferOptions',),
    # ('gmd:MD_Metadata','gmd:MD_Metadata','gmd:identificationInfo','gmd:MD_DataIdentification','gmd:citation', 'gmd:CI_Citation'):('identificationInfo'),

    # Extract resources from body (to _data)
    _extract_transfer_options(_body, opt, version, _data, errors, context)
    
    
    # BODY: iso19139 to iso translation

    # TODO the rest of the model

    
    # Update _data with changes
    _data.update({
        'type': TYPE_ISO
    })

    return _iso_profile, TYPE_ISO, opt, version, _data


def _extract_transfer_options(body, opt, version, data, errors, context):

    # _body = dict(body)
    _body = body
    # _data = dict(data)
    _transfer_options = get_nested(_body, ('gmd:MD_Metadata','gmd:distributionInfo','gmd:MD_Distribution','gmd:transferOptions',))
    #  = _data.pop(('transferOptions',))
    if _transfer_options:
        if not isinstance(_transfer_options, list):
            _transfer_options = [ _transfer_options ]
        for options in _transfer_options:

            # units = get_nested(options, ('gmd:unitsOfDistribution', 'gco:CharacterString',)) 
            # transferSize = get_nested(options, ('gmd:transferSize', 'gco:Real',))
            
            online = get_nested(options, ('gmd:MD_DigitalTransferOptions', 'gmd:onLine',))
            if not online:
                continue
            if isinstance(online, list):
                for idx, online_resource in enumerate(list(online)):
                    pop_online(online_resource, opt, TYPE_ONLINE_RESOURCE, version, data, errors, context)
                    online.remove(online_resource)
            else:
                pop_online(online, opt, type, version, data, errors, context)
                pop_nested(options, ('gmd:MD_DigitalTransferOptions', 'gmd:onLine',))

def pop_online(online_resource, opt, type, version, data, errors, context):
    if isinstance(online_resource, list):
            for resource in online_resource:
                get_online_resource(resource, opt, type, version, data, errors, context)
    else:
        get_online_resource(online_resource, opt, type, version, data, errors, context)

def get_online_resource(resource, opt, type, version, data, errors, context):
    r = resource.pop('gmd:CI_OnlineResource', None)
    if not r:
        return

    # we assume:
    # - body is an instance of gmd:CI_OnlineResource
    _body = dict(r)


    new_resource_body_fields = {
        # TODO otherwise do all here
        ('gmd:name', 'gco:CharacterString') : ('name',),
        ('gmd:description', 'gco:CharacterString') : ('description',),
        ('gmd:protocol', 'gco:CharacterString',) : ('protocol',),
        # ('gmd:linkage', 'gco:CharacterString') : ('linkage',),
    }
    _new_resource_body = {}
    errors = map_to(_body, new_resource_body_fields, _new_resource_body)


    # TODO recursive validation triggered by resource_create action ?
    new_resource_dict_fields = {
        # TODO otherwise do all here
        ('gmd:name','gco:CharacterString',) : ('name',),
        ('gmd:description','gco:CharacterString',) : ('description',),
        ('gmd:linkage','gmd:URL') : ('url',)
    }
    
    _new_resource_dict = {
        _c.SCHEMA_OPT_KEY: json.dumps(opt),
        _c.SCHEMA_VERSION_KEY: version,
        _c.SCHEMA_BODY_KEY: json.dumps(_new_resource_body),
        _c.SCHEMA_TYPE_KEY: type,
    }
    
    errors = map_to(_body, new_resource_dict_fields, _new_resource_dict)


    
    # new_resource.update({
    #     'format': _get_type_from(protocol, new_resource.get('url')) or ''
    # })

    resources = data.get('resources', [])
    resources.append(_new_resource_dict)
    data.update({'resources': resources})

    # TODO remove from body what is not managed by json
    
