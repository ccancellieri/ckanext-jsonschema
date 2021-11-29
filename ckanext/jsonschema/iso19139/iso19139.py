import ckan.lib.helpers as h
import ckan.plugins.toolkit as toolkit
_get_or_bust= toolkit.get_or_bust
_ = toolkit._
import ckan.plugins as p

import ckanext.jsonschema.validators as _v
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.interfaces as _i

# iso19139 extract/convert by default into the iso profile
from ckanext.jsonschema.iso19139.iso import TYPE_ISO,\
 TYPE_ISO_RESOURCE_ONLINE_RESOURCE, TYPE_ISO_RESOURCE_CITED_RESPONSIBLE_PARTY

import logging
log = logging.getLogger(__name__)

import json

#############################################

# TYPE_ONLINE_RESOURCE='online-resource'
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

#############################################

def __identification_info(identification_info, opt, version, data, errors, context):
    _identification_info = {}
    if identification_info.get('gmd:MD_DataIdentification'):
        identification_fields = {
            # DATA IDENTIFICATION ( citation see below )

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
            # ('gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:status','gmd:MD_ProgressCode','"@codeListValue',):('status',)
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
            # TODO seriespop_nested

            # ('gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:alternateTitle','gco:CharacterString'):('alternateTitle',)
        }
        # map body to ckan fields (_data)
        errors = _t.map_to(identification_info, identification_fields, _identification_info)

        citation = _t.get_nested(identification_info, ('gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation',))
        if citation:
            _citation = __citation(citation, opt, version, data, errors, context)
            _t.set_nested(_citation, ('citation',), _identification_info)
        
    return _citation
    
def __citation(citation, opt, version, data, errors, context):
    _citation = {}
    citation_fields = {
        ## DATA IDENTIFICATION ( citation )
        # title
        ('gmd:title','gco:CharacterString'):('citation','title',),
        # edition
        ('gmd:edition','gco:CharacterString',):('citation','edition',),

        # dates (see below)

        # TODO extract gmd:citedResponsibleParty
        # citedResponsibleParty (see below)

        # ## # TODO ASK about SERIES
        # # otherCitationDetails
        # ('gmd:collectiveTitle','gco:CharacterString'):('citation','series','otherCitationDetails'),
        # # collectiveTitle
        # ('gmd:collectiveTitle','gco:CharacterString'):('citation','series','collectiveTitle'),
        # # ISBN
        # ('gmd:collectiveTitle','gco:CharacterString'):('citation','series','ISBN'),
        # # ISSN
        # ('gmd:collectiveTitle','gco:CharacterString'):('citation','series','ISSN'),
        # ('gmd:collectiveTitle','gco:CharacterString'):('citation','series','name'),
        # ('gmd:collectiveTitle','gco:CharacterString'):('citation','series','issueIdentification'),
        # ('gmd:collectiveTitle','gco:CharacterString'):('citation','series','page'),


        # dates (see below)

        # presentationForm
        # TODO coud it be an array?
        ('gmd:presentationForm','gmd:CI_PresentationFormCode','@codeListValue',):('citation','presentationForm',),
    }
    errors = _t.map_to(citation, citation_fields, _citation)

    dates = _t.get_nested(citation, ('gmd:date',))
    if dates:
        _dates = __dates(dates)
        _t.set_nested(_citation, ('dates',), _dates)

    cited_responsible_party = _t.get_nested(citation, ('gmd:citedResponsibleParty',))
    if cited_responsible_party:
        _cited_responsible_parties = __cited_responsible_parties(cited_responsible_party, TYPE_ISO_RESOURCE_CITED_RESPONSIBLE_PARTY, opt, version, data, errors, context)
        # EXTRACTED TO RESOURCES NO NEED TO SET BACK INTO ISO

    return _citation

def __cited_responsible_parties(cited_responsible_party, _type, opt, version, data, errors, context):

    resources = data.get('resources', [])
    _cited_responsible_parties = []
    cited_responsible_parties = cited_responsible_party
    if not isinstance(cited_responsible_parties, list):
        cited_responsible_parties = [cited_responsible_party]
    for party in cited_responsible_parties:
        _p = {}
        party_fields = {
            # address
            ('gmd:CI_ResponsibleParty','gmd:contactInfo','gmd:CI_Contact','gmd:address','gmd:CI_Address','gmd:deliveryPoint','gco:CharacterString',):('contactInfo','address','deliveryPoint',),
            ('gmd:CI_ResponsibleParty','gmd:contactInfo','gmd:CI_Contact','gmd:address','gmd:CI_Address','gmd:city','gco:CharacterString',):('contactInfo','address','city',),
            ('gmd:CI_ResponsibleParty','gmd:contactInfo','gmd:CI_Contact','gmd:address','gmd:CI_Address','gmd:postalCode','gco:CharacterString',):('contactInfo','address','postalCode',),
            ('gmd:CI_ResponsibleParty','gmd:contactInfo','gmd:CI_Contact','gmd:address','gmd:CI_Address','gmd:country','gco:CharacterString',):('contactInfo','address','country',),
            ('gmd:CI_ResponsibleParty','gmd:contactInfo','gmd:CI_Contact','gmd:address','gmd:CI_Address','gmd:electronicMailAddress','gco:CharacterString',):('contactInfo','address','electronicMailAddress',),
            # phone
            ('gmd:CI_ResponsibleParty','gmd:contactInfo','gmd:CI_Contact','gmd:phone','gmd:voice','gco:CharacterString',):('phone','voice'),
            ('gmd:CI_ResponsibleParty','gmd:contactInfo','gmd:CI_Contact','gmd:phone','gmd:facsimile','gco:CharacterString',):('phone','facsimile'),
            # online resource
            ('gmd:CI_ResponsibleParty','gmd:contactInfo','gmd:CI_Contact','gmd:onlineResource','gmd:CI_OnlineResource', 'gmd:name', 'gco:CharacterString') : ('onlineResource', 'name',),
            ('gmd:CI_ResponsibleParty','gmd:contactInfo','gmd:CI_Contact','gmd:onlineResource','gmd:CI_OnlineResource', 'gmd:description', 'gco:CharacterString') : ('onlineResource', 'description',),
            ('gmd:CI_ResponsibleParty','gmd:contactInfo','gmd:CI_Contact','gmd:onlineResource','gmd:CI_OnlineResource', 'gmd:protocol', 'gco:CharacterString') : ('onlineResource', 'protocol',),
            ('gmd:CI_ResponsibleParty','gmd:contactInfo','gmd:CI_Contact','gmd:onlineResource','gmd:CI_OnlineResource', 'gmd:linkage', 'gco:CharacterString') : ('onlineResource', 'linkage',),
        }
        errors = _t.map_to(party, party_fields, _p)

        _new_resource_dict = {
            _c.SCHEMA_OPT_KEY: json.dumps(opt),
            _c.SCHEMA_VERSION_KEY: version,
            _c.SCHEMA_BODY_KEY: json.dumps(_p),
            _c.SCHEMA_TYPE_KEY: _type,
        }
        resources.append(_new_resource_dict)
        data.update({'resources': resources})

    return _cited_responsible_parties

def __dates(dates):
    _dates = []
    if not isinstance(dates, list):
        dates = [dates]
    for _date in dates:
        _d = {}
        dates_fields = {
            ('gmd:CI_Date','gmd:date','gco:Date',):('date',),
            ('gmd:CI_Date','gmd:dateType','gmd:CI_DateTypeCode','@codeListValue',):('dateType',),
        }
        errors = _t.map_to(_date, dates_fields, _d)

        _dates.append(_d)

    return _dates

def __spatial_representation_info(spatial_representation_info):
    # spatial_representation_info = _t.get_nested(body, ('gmd:MD_Metadata','gmd:spatialRepresentationInfo',))
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
            errors = _t.map_to(sri, grid_spatial_representation_info_fields, _sri)

            axis_dimension_properties = _t.get_nested(sri, ('gmd:MD_GridSpatialRepresentation','gmd:axisDimensionProperties',))
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
                errors = _t.map_to(axis, axis_fields, _axis)
                _dimensions.append(_axis)

        elif sri.get('gmd:MD_VectorSpatialRepresentation'):
            # VECTOR
            vector_spatial_representation_info_fields = {
                ('gmd:MD_VectorSpatialRepresentation','gmd:transformationParameterAvailability','gco:Boolean',):('transformationParameterAvailability',),
                ('gmd:MD_VectorSpatialRepresentation','gmd:cellGeometry','@codeListValue',):('cellGeometry',)
            }
            errors = _t.map_to(sri, vector_spatial_representation_info_fields, _sri)

            geometric_objects = _t.get_nested(sri, ('gmd:MD_VectorSpatialRepresentation','gmd:geometricObjects','gmd:MD_GeometricObjects',))
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
                errors = _t.map_to(go, go_fields, _go)
                _geometric_object.append(_go)
        else:
            continue

        _ret.append(_sri)
        
    return _ret

def _extract_iso(body, opt, version, data, errors, context):
    # DATA translation
    # root_fields = FrozenOrderedBidict({
    root_fields = {
        # fileIdentifier
        ('gmd:MD_Metadata','gmd:fileIdentifier','gco:CharacterString'):('fileIdentifier',),

        # language
        ('gmd:MD_Metadata','gmd:language','gmd:LanguageCode','@codeListValue',):('language',),
        
        # characterSet
        ('gmd:MD_Metadata','gmd:characterSet','gmd:MD_CharacterSetCode','@codeListValue',):('characterSet',),

        # metadataStandardName
        # TODO could this be an array?
        ('gmd:MD_Metadata','gmd:metadataStandardName','gco:CharacterString'):('metadataStandardName',),
        
        # metadataStandardVersion
        ('gmd:MD_Metadata','gmd:metadataStandardVersion','gco:CharacterString'):('metadataStandardVersion',),
        
        # parentIdentifier
        ('gmd:MD_Metadata','gco:CharacterString'):('parentIdentifier',),
        
        # dataIdentification (see below)
        
        # TODO license
        # <gmd:resourceConstraints>
        #     <gmd:MD_LegalConstraints>
        #         <gmd:useConstraints>
        #             <gmd:MD_RestrictionCode codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#MD_RestrictionCode" codeListValue="license"></gmd:MD_RestrictionCode>
        #         </gmd:useConstraints>
        #         <gmd:accessConstraints>
        #             <gmd:MD_RestrictionCode codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#MD_RestrictionCode" codeListValue="copyright"></gmd:MD_RestrictionCode>
        #         </gmd:accessConstraints>
        #         <gmd:otherConstraints>
        #             <gco:CharacterString>Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO. More info at \nhttps://creativecommons.org/licenses/by-nc-sa/3.0/igo/</gco:CharacterString>
        #         </gmd:otherConstraints>
        #     </gmd:MD_LegalConstraints>
        # </gmd:resourceConstraints>

        # referenceSystemIdentifier
        ('gmd:MD_Metadata','gmd:referenceSystemInfo','gmd:MD_ReferenceSystem','gmd:RS_Identifier','gmd:code','gco:CharacterString',):('referenceSystemIdentifier',),

        # spatialRepresentationInfo (see below)

        # dataQualityInfo
        ('gmd:MD_Metadata','gmd:dataQualityInfo','gmd:DQ_DataQuality','gmd:lineage','gmd:LI_Lineage','gmd:statement','gco:CharacterString',):('dataQualityInfo','lineage','statement',),
        ('gmd:MD_Metadata','gmd:dataQualityInfo','gmd:DQ_DataQuality','gmd:lineage','gmd:LI_Lineage','gmd:source','@uuidref',):('dataQualityInfo','lineage','source',),
        ('gmd:MD_Metadata','gmd:dataQualityInfo','gmd:DQ_DataQuality','gmd:scope','gmd:DQ_Scope','gmd:level','gmd:MD_ScopeCode','@codeListValue',):('dataQualityInfo','scope',),
    }
    _data = dict(data)
    _body = dict(body)
    _iso_profile = {}
    # map body to ckan fields (_data)
    errors = _t.map_to(_body, root_fields, _iso_profile)
    
    if errors:
        # TODO map errors {key,error} to ckan errors 
        # _v.stop_with_error('Unable to map to iso', errors)
        log.error('unable to map')

    spatial_representation_info = _t.get_nested(body, ('gmd:MD_Metadata','gmd:spatialRepresentationInfo',))
    if spatial_representation_info:
        _spatial_representation_info = __spatial_representation_info(spatial_representation_info)
        _t.set_nested(_iso_profile, ('spatialRepresentationInfo',), _spatial_representation_info)

    identification_info = _t.get_nested(body, ('gmd:MD_Metadata','gmd:identificationInfo',))
    if identification_info:
        _identification_info = __identification_info(identification_info, opt, version, data, errors, context)
        _t.set_nested(_iso_profile, ('dataIdentification',), _identification_info)

    # Extract resources from body (to _data)
    _extract_transfer_options(_body, opt, version, _data, errors, context)
    
    # Update _data type
    _data.update({
        'type': TYPE_ISO
    })

    return _iso_profile, TYPE_ISO, opt, version, _data

def _extract_transfer_options(body, opt, version, data, errors, context):

    # _body = dict(body)
    _body = body
    # _data = dict(data)
    _transfer_options = _t.get_nested(_body, ('gmd:MD_Metadata','gmd:distributionInfo','gmd:MD_Distribution','gmd:transferOptions',))
    #  = _data.pop(('transferOptions',))
    if _transfer_options:
        if not isinstance(_transfer_options, list):
            _transfer_options = [ _transfer_options ]
        for options in _transfer_options:

            # units = _t.get_nested(options, ('gmd:unitsOfDistribution', 'gco:CharacterString',)) 
            # transferSize = _t.get_nested(options, ('gmd:transferSize', 'gco:Real',))
            
            online = _t.get_nested(options, ('gmd:MD_DigitalTransferOptions', 'gmd:onLine',))
            if not online:
                continue
            if isinstance(online, list):
                for idx, online_resource in enumerate(list(online)):
                    pop_online(online_resource, opt, TYPE_ISO_RESOURCE_ONLINE_RESOURCE, version, data, errors, context)
                    online.remove(online_resource)
            else:
                pop_online(online, opt, type, version, data, errors, context)
                _t.pop_nested(options, ('gmd:MD_DigitalTransferOptions', 'gmd:onLine',))

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
    errors = _t.map_to(_body, new_resource_body_fields, _new_resource_body)


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
    
    errors = _t.map_to(_body, new_resource_dict_fields, _new_resource_dict)

    resources = data.get('resources', [])
    resources.append(_new_resource_dict)
    data.update({'resources': resources})
