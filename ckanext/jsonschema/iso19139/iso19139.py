from sqlalchemy.sql.expression import true
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
from ckanext.jsonschema.iso19139.iso import TYPE_ISO, TYPE_ISO_RESOURCE_DISTRIBUTOR,\
 TYPE_ISO_RESOURCE_ONLINE_RESOURCE, TYPE_ISO_RESOURCE_CITED_RESPONSIBLE_PARTY,\
     TYPE_ISO_RESOURCE_GRAPHIC_OVERVIEW, TYPE_ISO_RESOURCE_RESOURCE_CONTACT,\
         TYPE_ISO_RESOURCE_METADATA_CONTACT, TYPE_ISO_RESOURCE_MAINTAINER
            #  TYPE_ISO_RESOURCE_RESPONSIBLE_PARTY, TYPE_ISO_RESOURCE_DATASET

import logging
log = logging.getLogger(__name__)

import json

#############################################

# TYPE_ONLINE_RESOURCE='online-resource'
TYPE_ISO19139='iso19139'

SUPPORTED_DATASET_FORMATS = [TYPE_ISO19139]
SUPPORTED_RESOURCE_FORMATS = []


def _from_nested_list_extend_array(source, source_array_path, get_tuple_as_array, dest, dest_tuple):
    nested_items_root = _t.as_list_of_dict(source, filter = lambda x : _t.get_nested(x, source_array_path))
    if nested_items_root:
        for i in nested_items_root:
            _nested_element = _t.get_nested(i, source_array_path)
            nested_list = _t.as_list_of_values(_nested_element, get_tuple_as_array)
            _t.extend_nested(dest, dest_tuple, nested_list)
    
def _from_nested_list_extend_array_of_dict(source, source_array_path, get_mapping, dest, dest_tuple):
    nested_items_root = _t.as_list_of_dict(source, filter = lambda x : _t.get_nested(x, source_array_path))
    if nested_items_root:
        for i in nested_items_root:
            _nested_element = _t.get_nested(i, source_array_path)
            if _nested_element:
                nested_dicts = _t.as_list_of_dict(_nested_element, get_mapping)
                _t.extend_nested(dest, dest_tuple, nested_dicts)

def __identification_info(identification_info, opt, version, data, errors, context):
    _identification_info = {}
    if identification_info.get('gmd:MD_DataIdentification'):
        identification_fields = {
            # DATA IDENTIFICATION

            # citation (see below)

            ('gmd:MD_DataIdentification','gmd:abstract','gco:CharacterString'):('abstract',),
            ('gmd:MD_DataIdentification','gmd:purpose','gco:CharacterString'):('purpose',),
            ('gmd:MD_DataIdentification','gmd:status','gmd:MD_ProgressCode','@codeListValue',):('status',),

            # pointOfContact (see below)
            
            # resourceMaintenance maintenanceAndUpdateFrequency
            ('gmd:MD_DataIdentification','gmd:resourceMaintenance','gmd:MD_MaintenanceInformation','gmd:maintenanceAndUpdateFrequency','gmd:MD_MaintenanceFrequencyCode','@codeListValue'):('resourceMaintenance','maintenanceAndUpdateFrequency',),
            # resourceMaintenance (see below)
            
            # graphic-overview (see below) (resources)

            # descriptiveKeywords (see below)

            # resourceConstraints (see below)

            # spatialRepresentationType (see below)

            # spatialResolution (see below)

            # language
            ('gmd:MD_DataIdentification','gmd:language','gco:CharacterString',):('language',),
            # CharacterSet
            ('gmd:MD_DataIdentification','gmd:characterSet','gmd:MD_CharacterSetCode','@codeListValue',):('characterSet',),

            # topicCategory (see below)

            # extent (see below)

            # supplementalInformation
            ('gmd:MD_DataIdentification','gmd:supplementalInformation','gco:CharacterString',):('supplementalInformation',),

            # aggregationInfo (see below)

            # alternate title (not present into iso profile???)
            # ('gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation','gmd:alternateTitle','gco:CharacterString'):('alternateTitle',)
        }
        # map body to ckan fields (_data)
        errors = _t.map_to(identification_info, identification_fields, _identification_info)

        citation = _t.get_nested(identification_info, ('gmd:MD_DataIdentification','gmd:citation','gmd:CI_Citation',))
        if citation:
            _citation = __citation(citation, opt, version, data, errors, context)
            _t.set_nested(_identification_info, ('citation',), _citation)

        pointOfContact = _t.get_nested(identification_info, ('gmd:MD_DataIdentification','gmd:pointOfContact',))
        if pointOfContact:
            _pointOfContact = __responsible_parties(pointOfContact, TYPE_ISO_RESOURCE_RESOURCE_CONTACT, opt, version, data, errors, context)
            # EXTRACTED TO RESOURCES NO NEED TO SET BACK INTO ISO

        resourceMaintenance = _t.get_nested(identification_info, ('gmd:MD_DataIdentification','gmd:resourceMaintenance','gmd:contact',))
        if resourceMaintenance:
            _resourceMaintenance = __responsible_parties(resourceMaintenance, TYPE_ISO_RESOURCE_MAINTAINER, opt, version, data, errors, context)
            # EXTRACTED TO RESOURCES NO NEED TO SET BACK INTO ISO

        graphic_overview = _t.get_nested(identification_info, ('gmd:MD_DataIdentification','gmd:graphicOverview',))
        if graphic_overview:
            _graphic_overview = __graphic_overview(graphic_overview, TYPE_ISO_RESOURCE_GRAPHIC_OVERVIEW, opt, version, data, errors, context)
            # EXTRACTED TO RESOURCES NO NEED TO SET BACK INTO ISO

        descriptiveKeywords = _t.get_nested(identification_info, ('gmd:MD_DataIdentification','gmd:descriptiveKeywords',))
        if descriptiveKeywords:
            _descriptiveKeywords = __descriptiveKeywords(descriptiveKeywords, opt, version, data, errors, context)
            _t.set_nested(_identification_info, ('descriptiveKeywords',), _descriptiveKeywords)

        resourceConstraints = _t.get_nested(identification_info, ('gmd:MD_DataIdentification','gmd:resourceConstraints',))
        if resourceConstraints:
            
            _from_nested_list_extend_array(resourceConstraints,
                ('gmd:MD_LegalConstraints','gmd:otherConstraints',),
                ('gco:CharacterString',),
                _identification_info,
                ('resourceConstraints','legalConstraints','otherConstraints',))
            
            _from_nested_list_extend_array(resourceConstraints,
                ('gmd:MD_LegalConstraints','gmd:useLimitation',),
                ('gco:CharacterString',),
                _identification_info,
                ('resourceConstraints','legalConstraints','useLimitation',))

            _from_nested_list_extend_array(resourceConstraints,
                ('gmd:MD_LegalConstraints','gmd:useConstraints',),
                ('gmd:MD_RestrictionCode','@codeListValue',),
                _identification_info,
                ('resourceConstraints','legalConstraints','useConstraints',))

            _from_nested_list_extend_array(resourceConstraints,
                ('gmd:MD_LegalConstraints','gmd:accessConstraints',),
                ('gmd:MD_RestrictionCode','@codeListValue',),
                _identification_info,
                ('resourceConstraints','legalConstraints','accessConstraints',))
                    
            # MD_SecurityConstraints
            #     ('gmd:MD_SecurityConstraints','gmd:useLimitation','gco:CharacterString',):('securityConstraints','useLimitation',),
            _from_nested_list_extend_array(resourceConstraints,
                ('gmd:MD_SecurityConstraints','gmd:useLimitation',),
                ('gco:CharacterString',),
                _identification_info,
                ('resourceConstraints','securityConstraints','useLimitation',))

                # ('gmd:MD_SecurityConstraints','gmd:classification','gco:MD_ClassificationCode','@codeListValue',):('securityConstraints','classification',),
            _from_nested_list_extend_array(resourceConstraints,
                ('gmd:MD_SecurityConstraints','gmd:classification',),
                ('gco:MD_ClassificationCode','@codeListValue',),
                _identification_info,
                ('resourceConstraints','securityConstraints','classification',))

            _from_nested_list_extend_array(resourceConstraints,
                ('gmd:MD_SecurityConstraints','gmd:userNote',),
                ('gco:CharacterString',),
                _identification_info,
                ('resourceConstraints','securityConstraints','userNote',))

            _from_nested_list_extend_array(resourceConstraints,
                ('gmd:MD_SecurityConstraints','gmd:classificationSystem',),
                ('gco:CharacterString',),
                _identification_info,
                ('resourceConstraints','securityConstraints','classificationSystem',))

            _from_nested_list_extend_array(resourceConstraints,
                ('gmd:MD_SecurityConstraints','gmd:useLimitation',),
                ('gco:CharacterString',),
                _identification_info,
                ('resourceConstraints','securityConstraints','useLimitation',))
            
            _from_nested_list_extend_array(resourceConstraints,
                ('gmd:MD_SecurityConstraints','gmd:handlingDescription',),
                ('gco:CharacterString',),
                _identification_info,
                ('resourceConstraints','securityConstraints','handlingDescription',))
            
            # MD_Constraints
            # ('gmd:MD_Constraints','gmd:useLimitation','gco:CharacterString',):('useLimitation',),
            _from_nested_list_extend_array(resourceConstraints,
                ('gmd:MD_Constraints','gmd:useLimitation',),
                ('gco:CharacterString',),
                _identification_info,
                ('resourceConstraints','constraints','useLimitation',))

        # spatialRepresentationType
        _from_nested_list_extend_array(identification_info,
                ('gmd:MD_DataIdentification','gmd:spatialRepresentationType',),
                ('gmd:MD_SpatialRepresentationTypeCode','@codeListValue',),
                _identification_info,
                ('spatialRepresentationType',))

        _resolution_fields_map = {
            ('gmd:MD_Resolution','gmd:distance','gco:Distance','#text',):('distance',),
            ('gmd:MD_Resolution','gmd:distance','gco:Distance','@uom',):('unit',),
            ('gmd:MD_Resolution','gmd:equivalentScale','gmd:MD_RepresentativeFraction','gmd:denominator','gco:Integer',):('scaleDenominator',),
        }
        _from_nested_list_extend_array_of_dict(identification_info,
                ('gmd:MD_DataIdentification','gmd:spatialResolution',),
                _resolution_fields_map,
                _identification_info,
                ('spatialResolution',))
        
        topicCategory = _t.get_nested(identification_info, ('gmd:MD_DataIdentification','gmd:topicCategory',))
        if topicCategory:
            _topicCategory = _t.as_list_of_values(topicCategory, ('gmd:MD_TopicCategoryCode',))
            _t.set_nested(_identification_info, ('topicCategory',), _topicCategory)

        # extent
        extents = _t.get_nested(identification_info, ('gmd:MD_DataIdentification','gmd:extent',))
        if not isinstance(extents, list):
            extents = [ extents ]
        for extent in extents:
            _extent_geographic_bbox_fields_map = {
                ('gmd:EX_GeographicBoundingBox','gmd:westBoundLongitude','gco:Decimal',):('geographic','bbox','west',),
                ('gmd:EX_GeographicBoundingBox','gmd:eastBoundLongitude','gco:Decimal',):('geographic','bbox','east',),
                ('gmd:EX_GeographicBoundingBox','gmd:southBoundLatitude','gco:Decimal',):('geographic','bbox','south',),
                ('gmd:EX_GeographicBoundingBox','gmd:northBoundLatitude','gco:Decimal',):('geographic','bbox','north',)
            }
            _from_nested_list_extend_array_of_dict(extent,
                    ('gmd:EX_Extent','gmd:geographicElement',),
                    _extent_geographic_bbox_fields_map,
                    _identification_info,
                    ('extent',))

            _extent_geographic_polygon_fields_map = {
                ('gmd:EX_BoundingPolygon','gmd:polygon','gml:MultiSurface','gml:surfaceMember','gml:Polygon','gml:exterior','gml:LinearRing','gml:posList','#text',):('geographic','polygon','geospatial',),
            }
            _from_nested_list_extend_array_of_dict(extent,
                    ('gmd:EX_Extent','gmd:geographicElement',),
                    _extent_geographic_polygon_fields_map,
                    _identification_info,
                    ('extent',))

            # TODO on 1/12/2021 we decided to delay the management of this type of item
            # extent_vertical = _t.get_nested(identification_info, ('gmd:MD_DataIdentification','gmd:extent','gmd:EX_Extent',))
            # if extent_vertical:
            #     # vertical
            #     extent_vertical_filter = lambda r : r.get('gmd:verticalElement') is not None
            #     extent_vertical_fields = {
            #         ('gmd:verticalElement','gmd:EX_VerticalExtent','#####',):('scaleDenominator',),
            #     }
            #     _extent_vertical = _t.as_list_of_dict(extent_vertical, extent_vertical_fields, errors, extent_vertical_filter)

            _extent_temporal_fields_map = {
                ('gmd:EX_TemporalExtent','gmd:extent','gml:TimePeriod','gml:beginPosition',):('temporal','beginDate',),
                ('gmd:EX_TemporalExtent','gmd:extent','gml:TimePeriod','gml:endPosition',):('temporal','endDate',),
            }
            _from_nested_list_extend_array_of_dict(extent,
                    ('gmd:EX_Extent','gmd:temporalElement',),
                    _extent_temporal_fields_map,
                    _identification_info,
                    ('extent',))

        aggregationInfo = _t.get_nested(identification_info, ('gmd:MD_DataIdentification','gmd:aggregationInfo',))
        if aggregationInfo:
            aggregationInfo_fields = {
                ('gmd:MD_AggregateInformation','gmd:associationType','gmd:DS_AssociationTypeCode','codeListValue',):('aggregationInfo','associationType',),
                ('gmd:MD_AggregateInformation','gmd:aggregateDataSetIdentifier','gmd:MD_Identifier','gmd:code','gco:CharacterString',):('aggregationInfo','code',)
            }
            _aggregationInfo = _t.as_list_of_dict(aggregationInfo, aggregationInfo_fields)
            _t.set_nested(_identification_info, ('aggregationInfo',), _aggregationInfo)
    
    # _t.set_nested(_citation, ('identificationInfo',), _identification_info)

    return _identification_info
    
def __citation(citation, opt, version, data, errors, context):
    _citation = {}
    citation_fields = {
        ## DATA IDENTIFICATION ( citation )
        # title
        ('gmd:title','gco:CharacterString',):('title',),
        # edition
        ('gmd:edition','gco:CharacterString',):('edition',),

        # dates (see below)

        # citedResponsibleParty (see below)

        # # SERIES
        # name
        ('gmd:series','gmd:CI_Series','gmd:name','gco:CharacterString',):('series','name',),
        # issueIdentification
        ('gmd:series','gmd:CI_Series','gmd:issueIdentification','gco:CharacterString',):('series','issueIdentification',),
        # page
        ('gmd:series','gmd:CI_Series','gmd:page','gco:CharacterString',):('series','page',),
        
        # otherCitationDetails
        ('gmd:otherCitationDetails','gco:CharacterString',):('otherCitationDetails',),
        # collectiveTitle
        ('gmd:collectiveTitle','gco:CharacterString',):('collectiveTitle',),
        # ISBN
        ('gmd:ISBN','gco:CharacterString',):('ISBN',),
        # ISSN
        ('gmd:ISSN','gco:CharacterString',):('ISSN',),

        # presentationForm (see below)
        
    }
    errors = _t.map_to(citation, citation_fields, _citation)

    # TODO use _t.as_list_of_dict
    dates = _t.get_nested(citation, ('gmd:date',))
    if dates:
        _dates = __dates(dates)
        _t.set_nested(_citation, ('dates',), _dates)

    presentationForm = _t.get_nested(citation, ('gmd:presentationForm',))
    if presentationForm:
        _t.set_nested(_citation, ('presentationForm',), _t.as_list_of_values(presentationForm, ('gmd:CI_PresentationFormCode','@codeListValue',)))
    
    cited_responsible_party = _t.get_nested(citation, ('gmd:citedResponsibleParty',))
    if cited_responsible_party:
        _cited_responsible_parties = __responsible_parties(cited_responsible_party, TYPE_ISO_RESOURCE_CITED_RESPONSIBLE_PARTY, opt, version, data, errors, context)
        # EXTRACTED TO RESOURCES NO NEED TO SET BACK INTO ISO

    return _citation

def __responsible_parties(cited_responsible_party, _type, opt, version, data, errors, context):

    resources = data.get('resources', [])
    _responsible_parties = []
    responsible_parties = cited_responsible_party
    if not isinstance(responsible_parties, list):
        responsible_parties = [cited_responsible_party]
    for party in responsible_parties:
        _p = {}
        party_fields = {
            # individualName
            ('gmd:CI_ResponsibleParty','gmd:individualName','gco:CharacterString',):('individualName',),
            # organisationName
            ('gmd:CI_ResponsibleParty','gmd:organisationName','gco:CharacterString',):('organisationName',),
            # positionName
            ('gmd:CI_ResponsibleParty','gmd:positionName','gco:CharacterString',):('positionName',),
            # role
            ('gmd:CI_ResponsibleParty','gmd:role','gmd:CI_RoleCode','@codeListValue',):('role',),
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

        _url = _t.get_nested(_p,('onlineResource', 'linkage',)) or  ''

        _new_resource_dict = {
            _c.SCHEMA_OPT_KEY: json.dumps(opt),
            _c.SCHEMA_VERSION_KEY: version,
            _c.SCHEMA_BODY_KEY: json.dumps(_p),
            _c.SCHEMA_TYPE_KEY: _type,
            'url': _url
        }
        resources.append(_new_resource_dict)

    data.update({'resources': resources})
    return _responsible_parties


def __graphic_overview(graphic_overview, _type, opt, version, data, errors, context):

    resources = data.get('resources', [])
    _graphic_overview = []
    graphic_overview = graphic_overview
    if not isinstance(graphic_overview, list):
        graphic_overview = [graphic_overview]
    for go in graphic_overview:
        _p = {}
        graphic_overview_fields = {
            # url
            # ('gmd:MD_BrowseGraphic','gmd:fileName','gco:CharacterString',):('url',),
            # fileDescription
            ('gmd:MD_BrowseGraphic','gmd:fileDescription','gco:CharacterString',):('fileDescription',),
        }
        errors = _t.map_to(go, graphic_overview_fields, _p)

        _new_resource_dict = {
            _c.SCHEMA_OPT_KEY: json.dumps(opt),
            _c.SCHEMA_VERSION_KEY: version,
            _c.SCHEMA_BODY_KEY: json.dumps(_p),
            _c.SCHEMA_TYPE_KEY: _type,
            'url': _t.get_nested(go, ('gmd:MD_BrowseGraphic','gmd:fileName','gco:CharacterString',)) or ''
        }
        resources.append(_new_resource_dict)

    data.update({'resources': resources})
    return _graphic_overview

def __descriptiveKeywords(descriptiveKeywords, opt, version, data, errors, context):
    _descriptiveKeywords = []
    if not isinstance(descriptiveKeywords, list):
        descriptiveKeywords = [descriptiveKeywords]
    for _dk in descriptiveKeywords:
        _k = {}
        descriptiveKeywords_fields = {
            ('gmd:MD_Keywords','gmd:type','gmd:MD_KeywordTypeCode','@codeListValue',):('type',),
            # keywords (see below)
        }
        _t.map_to(_dk,descriptiveKeywords_fields,_k)
        _keywords = _t.get_nested(_dk, ('gmd:MD_Keywords','gmd:keyword',))
        _ks = _t.as_list_of_values(_keywords, ('gco:CharacterString',))
        _t.set_nested(_k, ('keywords',), _ks)

        _descriptiveKeywords.append(_k)
    return _descriptiveKeywords

# TODO use _t.as_list_of_dict
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
        # convert types
        # not json serializable
#        _t.as_datetime(_d, ('date',))
        _dates.append(_d)

    return _dates

def __spatial_representation_info(spatial_representation_info):
    # spatial_representation_info = _t.get_nested(body, ('gmd:MD_Metadata','gmd:spatialRepresentationInfo',))
    _Grids = []
    _Vectors = []
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

            # convert types
            _t.as_boolean(_sri, ('transformationParameterAvailability',))

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
            
            _Grids.append(_sri)

        elif sri.get('gmd:MD_VectorSpatialRepresentation'):
            # VECTOR<gmd:MD_VectorSpatialRepresentation>
            vector_spatial_representation_info_fields = {
                ('gmd:MD_VectorSpatialRepresentation','gmd:topologyLevel','gmd:MD_TopologyLevelCode','@codeListValue',):('topologyLevel',)
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
            _Vectors.append(_sri)
        else:
            continue

    _ret = {}
    if _Vectors:
        _ret = { 'vectorSpatialRepresentation' : _Vectors }
    if _Grids:
        _ret.update({ 'gridSpatialRepresentation' : _Grids })
    return _ret

def _extract_iso(body, opt, version, data, errors, context):
    # DATA translation
    # root_fields = FrozenOrderedBidict({

    _data = dict(data)
    _body = dict(body)
    _iso_profile = {}
    _iso_profile_fields = {
        # fileIdentifier
        ('gmd:MD_Metadata','gmd:fileIdentifier','gco:CharacterString'):('fileIdentifier',),
        # TODO
        #  
        # "gmd:fileIdentifier":{
        #     "gco:CharacterString":{
        #         "@xmlns:gmx":"http://www.isotc211.org/2005/gmx",
        #         "#text":"dcc718a7-xyz-4c86-xyz-6abfxyz---70db",
        #         "@xmlns:srv":"http://www.isotc211.org/2005/srv"
        #     }
        # },

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
        ('gmd:MD_Metadata','gmd:parentIdentifier','gco:CharacterString'):('parentIdentifier',),
        
        # dataIdentification (see below)
        
        # referenceSystemIdentifier
        ('gmd:MD_Metadata','gmd:referenceSystemInfo','gmd:MD_ReferenceSystem','gmd:RS_Identifier','gmd:code','gco:CharacterString',):('referenceSystemIdentifier',),

        # spatialRepresentationInfo (see below)

        # DISTRIBUTION INFO
        # transferOptions (see below) _extract_transfer_options

        # distributionFormat (see below) _distribution_format
        
        # distributor (see below) _extract_distributor

        # from xml to resource -> gmd:contact (see below)

        # dataQualityInfo
        ('gmd:MD_Metadata','gmd:dataQualityInfo','gmd:DQ_DataQuality','gmd:lineage','gmd:LI_Lineage','gmd:statement','gco:CharacterString',):('dataQualityInfo','lineage','statement',),
        ('gmd:MD_Metadata','gmd:dataQualityInfo','gmd:DQ_DataQuality','gmd:lineage','gmd:LI_Lineage','gmd:source','@uuidref',):('dataQualityInfo','lineage','source',),
        ('gmd:MD_Metadata','gmd:dataQualityInfo','gmd:DQ_DataQuality','gmd:scope','gmd:DQ_Scope','gmd:level','gmd:MD_ScopeCode','@codeListValue',):('dataQualityInfo','scope',),
    }
    # map body to ckan fields (_data)
    errors = _t.map_to(_body, _iso_profile_fields, _iso_profile)
    
    if errors:
        # TODO map errors {key,error} to ckan errors 
        # _v.stop_with_error('Unable to map to iso', errors)
        log.error('unable to map')

    spatial_representation_info = _t.get_nested(body, ('gmd:MD_Metadata','gmd:spatialRepresentationInfo',))
    if spatial_representation_info:
        _spatial_representation_info = __spatial_representation_info(spatial_representation_info)
        _t.set_nested(_iso_profile, ('spatialRepresentationInfo',), _spatial_representation_info)

    contact = _t.get_nested(body, ('gmd:MD_Metadata','gmd:contact',))
    if contact:
        _contact = __responsible_parties(contact, TYPE_ISO_RESOURCE_METADATA_CONTACT, opt, version, _data, errors, context)
        # EXTRACTED TO RESOURCES NO NEED TO SET BACK INTO ISO

    identification_info = _t.get_nested(body, ('gmd:MD_Metadata','gmd:identificationInfo',))
    if identification_info:
        _identification_info = __identification_info(identification_info, opt, version, _data, errors, context)
        _t.set_nested(_iso_profile, ('dataIdentification',), _identification_info)

    # Extract resources from body (to _data)
    _extract_transfer_options(_body, opt, version, _data, errors, context)
    
    distributionFormat = _t.get_nested(body, ('gmd:MD_Metadata','gmd:distributionInfo','gmd:MD_Distribution','gmd:distributionFormat',))
    if distributionFormat:
        distributionFormat_fields = {
            ('gmd:MD_Format','gmd:name','gco:CharacterString',) : ('name',),
            ('gmd:MD_Format','gmd:version','gco:CharacterString',) : ('version',),
        }
        _distributionFormat = _t.as_list_of_dict(distributionFormat, distributionFormat_fields)
        _t.set_nested(_iso_profile, ('distributionFormat',), _distributionFormat)

    # distributor
    distributor = _t.get_nested(body, ('gmd:MD_Metadata','gmd:distributionInfo','gmd:MD_Distribution','gmd:distributor',))
    if distributor:
        _distributor = _extract_distributor(distributor, TYPE_ISO_RESOURCE_DISTRIBUTOR, opt, version, _data, errors, context)
        # EXTRACTED TO RESOURCES NO NEED TO SET BACK INTO ISO

    # Update _data type
    _data.update({
        'type': TYPE_ISO
    })

    return _iso_profile, TYPE_ISO, opt, version, _data

def _extract_distributor(distributor, _type, opt, version, data, errors, context):

    if not isinstance(distributor, list):
        distributor = [distributor]
    for distrib in distributor:
        # TODO ??? gmd:distributorFormat
        _distributor_contact = _t.get_nested(distrib, ('gmd:MD_Distributor','gmd:distributorContact',))
        if _distributor_contact:
            __responsible_parties(_distributor_contact, _type, opt, version, data, errors, context)
            return True
    
def _extract_transfer_options(body, opt, version, data, errors, context):

    _body = body
    _transfer_options = _t.get_nested(_body, ('gmd:MD_Metadata','gmd:distributionInfo','gmd:MD_Distribution','gmd:transferOptions',))
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
                pop_online(online, opt, TYPE_ISO_RESOURCE_ONLINE_RESOURCE, version, data, errors, context)
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


class JsonschemaIso19139(p.SingletonPlugin):
    p.implements(_i.IBinder, inherit=True)

    def extract_id(self, body, type, opt, version, errors, context):
        if type == TYPE_ISO19139:
            identification_info = _t.get_nested(body, ('gmd:MD_Metadata','gmd:fileIdentifier','gco:CharacterString'))
            return identification_info

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