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

import ckan.lib.navl.dictization_functions as df
import uuid
config = toolkit.config

TYPE_ISO = 'iso'

SUPPORTED_DATASET_FORMATS = [TYPE_ISO]

TYPE_ISO_RESOURCE_DATASET = 'resource-dataset'
TYPE_ISO_ONLINE_RESOURCE = 'online-resource'
TYPE_ISO_RESOURCE_RESPONSIBLE = 'responsible'
TYPE_ISO_RESOURCE_MAINTENANCE = 'resource-maintenance'
TYPE_ISO_RESOURCE_POINT_OF_CONTACT = 'point-of-contact'
TYPE_ISO_RESOURCE_CITED_RESPONSIBLE = 'cited-responsible'

SUPPORTED_ISO_RESOURCE_FORMATS = [
    TYPE_ISO_ONLINE_RESOURCE,
    TYPE_ISO_RESOURCE_DATASET,
    TYPE_ISO_RESOURCE_RESPONSIBLE,
    TYPE_ISO_RESOURCE_MAINTENANCE,
    TYPE_ISO_RESOURCE_POINT_OF_CONTACT,
    TYPE_ISO_RESOURCE_CITED_RESPONSIBLE
    ]

# ISO_VOCABULARY={}

# ISO_OPT={}

class JsonschemaIso(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(_i.IBinder, inherit = True)

    # IConfigurer

    def update_config(self, config_):
        # ISO_VOCABULARY = {
        #     # topic category:
        #     # ---------------
        #     'creation' : _vocabulary_setup('iso_creation'),
        #     'publication' : _vocabulary_setup('iso_publication'),
        #     'revision' : _vocabulary_setup('iso_revision'),
        #     # MD_KeywordTypeCode:
        #     # -------------------
        #     'discipline' : _vocabulary_setup('iso_discipline'),
        #     'place' : _vocabulary_setup('iso_place'),
        #     'stratum' : _vocabulary_setup('iso_stratum'),
        #     'temporal' : _vocabulary_setup('iso_temporal'),
        #     'theme' : _vocabulary_setup('iso_theme')
        # }
        
        pass
        #TODO

    # IBinder

    def supported_resource_types(self, dataset_type, opt=_c.SCHEMA_OPT, version=_c.SCHEMA_VERSION):

        if version != _c.SCHEMA_VERSION:
            log.warn('Version: \'{}\' is not supported by this plugin ({})'.format(version, __name__))
            # when version is not the default one we don't touch
            return []
        # TODO MAPPING
        if dataset_type == TYPE_ISO:
            return SUPPORTED_ISO_RESOURCE_FORMATS
        return []
        
    def supported_dataset_types(self, opt, version):
        if version != _c.SCHEMA_VERSION:
            # when version is not the default one we don't touch
            return []

        return SUPPORTED_DATASET_FORMATS

    def extract_from_json(self, body, type, opt, version, key, data, errors, context):
        if type == TYPE_ISO:
            self._extract_from_iso(body, type, opt, version, key, data, errors, context)
            return
        elif type == TYPE_ISO_ONLINE_RESOURCE:
            _extract_iso_online_resource(body, type, opt, version, key, data, errors, context)
            return
        elif type == TYPE_ISO_RESOURCE_DATASET:
            _extract_iso_resource_dataset(body, type, opt, version, key, data, errors, context)
            return
        elif type == TYPE_ISO_RESOURCE_RESPONSIBLE:
            _extract_iso_resource_responsible(body, type, opt, version, key, data, errors, context)
            return
        elif type == TYPE_ISO_RESOURCE_MAINTENANCE:
            _extract_iso_resource_responsible(body, type, opt, version, key, data, errors, context)
            return
        elif type == TYPE_ISO_RESOURCE_POINT_OF_CONTACT:
            _extract_iso_resource_responsible(body, type, opt, version, key, data, errors, context)
            return
        elif type == TYPE_ISO_RESOURCE_CITED_RESPONSIBLE:
            _extract_iso_resource_responsible(body, type, opt, version, key, data, errors, context)
            return
        
        
        
    def _extract_from_iso(self, body, type, opt, version, key, data, errors, context):
        # if key==('name',):
        _data = df.unflatten(data)

        _extract_iso_name(body, type, opt, version, key, _data, errors, context)
        
        # TODO

        data.update(df.flatten_dict(_data))


def _extract_iso_name(body, opt, type, version, key, data, errors, context):

    # TODO generate if still none...
    # munge title to package name
    # For taking a title of a package and munging it to a readable and valid dataset id. Symbols and whitespeace are converted into dashes, with multiple dashes collapsed. Ensures that long titles with a year at the end preserves the year should it need to be shortened. Example:

    # /api/util/dataset/munge_title_to_name?title=police:%20spending%20figures%202009
    
    name = str(body.get('fileIdentifier',uuid.uuid4()))
    name = name or data.get('name') #TODO error if null...
    # notes = str(body.get('description',''))

    if not name:
        _v.stop_with_error('Unable to obtain {}'.format(key), key, errors)
        
    _dict = {
        'name': name,
        'url': h.url_for(controller = 'package', action = 'read', id = name, _external = True),
    }
    data.update(_dict)

######################################################
## RESOURCES
######################################################

def _extract_iso_online_resource(body, opt, type, version, key, data, errors, context):
    # TODO
    name = str(body.get('name',uuid.uuid4()))
    name = name or data.get('name') #TODO error if null...
    if not name:
        _v.stop_with_error('Unable to obtain {}'.format(key), key, errors)
    
    description = str(body.get('role',''))

    _dict = {
        'name': name,
        'description': description,
        'format': _get_format(str(body.get('protocol','')), data.get('url',''))
    }
    data.update(_dict)

def _extract_iso_resource_dataset(body, opt, type, version, key, data, errors, context):

    name = str(body.get('name',uuid.uuid4()))
    name = name or data.get('name') #TODO error if null...

    if not name:
        _v.stop_with_error('Unable to obtain {}'.format(key), key, errors)
        
    _dict = {
        'name': name
    }
    data.update(_dict)

def _extract_iso_resource_responsible(body, opt, type, version, key, data, errors, context):

    name = str(body.get('individualName'))
    name = name or data.get('name') #TODO error if null...
    if not name:
        _v.stop_with_error('Unable to obtain name', key, errors)
    
    description = str(body.get('role'))
    description = data.get('description', description) #TODO error if null...

    _dict = {
        'name': name,
        'description': description
    }
    data.update(_dict)

def _get_format(protocol = None, url = None):
    
    # https://www.ogc.org/docs/is
    # https://geonetwork-opensource.org/manuals/3.10.x/en/annexes/standards/iso19139.html#protocol
    protocols = {
        'esri:aims-http-configuration':'http',
        'esri:aims-http-get-feature':'http', #arcims internet feature map service
        'esri:aims-http-get-image':'http', # arcims internet image map service
        'glg:kml-2.0-http-get-map':'kml', # google earth kml service (ver 2.0)
        'ogc:csw':'csw', # ogc-csw catalogue service for the web
        'ogc:kml':'kml', # ogc-kml keyhole markup language
        'ogc:gml':'gml', # ogc-gml geography markup language
        #'ogc:ods':'', # ogc-ods openls directory service
        #'ogc:ogs':'', # ogc-ods openls gateway service
        #'ogc:ous':'', # ogc-ods openls utility service
        #'ogc:ops':'', # ogc-ods openls presentation service
        #'ogc:ors':'', # ogc-ods openls route service
        #'ogc:sos':'', # ogc-sos sensor observation service
        #'ogc:sps':'', # ogc-sps sensor planning service
        #'ogc:sas':'', # ogc-sas sensor alert service
        'ogc:wcs':'wcs', # ogc-wcs web coverage service
        'ogc:wcs-1.1.0-http-get-capabilities':'wcs', # ogc-wcs web coverage service (ver 1.1.0)
        'ogc:wcts':'wcts', # ogc-wcts web coordinate transformation service
        'ogc:wfs':'wfs', # ogc-wfs web feature service
        'ogc:wfs-1.0.0-http-get-capabilities':'wfs', # ogc-wfs web feature service (ver 1.0.0)
        'ogc:wfs-g':'wfs', # ogc-wfs-g gazzetteer service
        'ogc:wmc':'wmc', # ogc-wmc web map context
        'ogc:wms':'wms', # ogc-wms web map service
        'ogc:wms-1.1.1-http-get-capabilities':'wms', # ogc-wms capabilities service (ver 1.1.1)
        'ogc:wms-1.3.0-http-get-capabilities':'wms', # ogc-wms capabilities service (ver 1.3.0)
        'ogc:wms-1.1.1-http-get-map':'wms', # ogc web map service (ver 1.1.1)
        'ogc:wms-1.3.0-http-get-map':'wms', # ogc web map service (ver 1.3.0)
        'ogc:wmts':'wmts', # ogc-wmts web map tiled service
        'ogc:wmts-1.0.0-http-get-capabilities':'wmts', # ogc-wmts capabilities service (ver 1.0.0)
        'ogc:sos-1.0.0-http-get-observation':'sos', # ogc-sos get observation (ver 1.0.0)
        'ogc:sos-1.0.0-http-post-observation':'sos', # ogc-sos get observation (post) (ver 1.0.0)
        'ogc:wns':'wns', # ogc-wns web notification service
        'ogc:wps':'wps', # ogc-wps web processing service
        #'ogc:ows-c':'', # ogc ows context
        'tms':'tms', # tiled map service
        'www:download-1.0-ftp-download':'ftp', # file for download through ftp
        'www:download-1.0-http-download':'http', # file for download
        #'file:geo':'', # gis file
        #'file:raster':'', # gis raster file
        'www:link-1.0-http-ical':'ical', # icalendar (url)
        'www:link-1.0-http-link':'http', # web address (url)
        #'doi':'', # digital object identifier (doi)
        'www:link-1.0-http-partners':'http', # partner web address (url)
        'www:link-1.0-http-related':'http', # related link (url)
        'www:link-1.0-http-rss':'http', # rss news feed (url)
        'www:link-1.0-http-samples':'http', # showcase product (url)
        #'db:postgis':'', # postgis database table
        #'db:oracle':'', # oracle database table
        'www:link-1.0-http-opendap':'http', # opendap url
        'www:link':'http',
        #'rbnb:dataturbine':'', # data turbine
        #'ukst':'', # unknown service type
    }
    if protocol:
        if not isinstance(protocol, str):
            protocol = str(protocol)
        resource_type = protocols.get(protocol.lower().strip())
        if resource_type:
            return resource_type

    resource_types = {
        # OGC
        'wms': ('/wms', 'service=wms', 'geoserver/wms', 'mapserver/wmsserver', 'com.esri.wms.Esrimap', 'service/wms'),
        'wfs': ('/wfs', 'service=wfs', 'geoserver/wfs', 'mapserver/wfsserver', 'com.esri.wfs.Esrimap'),
        'wcs': ('/wcs', 'service=wcs', 'geoserver/wcs', 'imageserver/wcsserver', 'mapserver/wcsserver'),
        'sos': ('/sos', 'service=sos',),
        'csw': ('/csw', 'service=csw',),
        # ESRI
        'kml': ('mapserver/generatekml',),
        'arcims': ('com.esri.esrimap.esrimap',),
        'arcgis_rest': ('arcgis/rest/services',),
    }

    if url:
        if not isinstance(url, str):
            url = str(url)
        url = url.lower().strip()
        for resource_type, parts in resource_types.items():
            if any(part in url for part in parts):
                return resource_type

        file_types = {
            'kml' : 'kml',
            'kmz': 'kmz',
            'gml': 'gml',
            'tif': 'tif',
            'tiff': 'tif',
            'json': 'json',
            'shp': 'shp',
            'zip': 'zip',
            'jpg': 'jpg',
            'jpeg': 'jpg',
            'png': 'png',
        }

        import os
        splitted_url = os.path.splitext(url)
        if len(splitted_url) > 1:
            extension = splitted_url[1][1:]
            if extension:
                return file_types.get(extension)






#######################################
## UNUSED
#######################################


def _vocabulary_setup(vocab_name, tags=[], context={}):
    # user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    # context = {'user': user['name']}
    context.update({'ignore_auth': True})
    try:
        data = {'id': vocab_name}
        return toolkit.get_action('vocabulary_show')(context, data)
    except Exception as e:
        log.warn('Error getting vocabulary: {}'.format(str(e)))
    # toolkit.ObjectNotFound:
        data = {'name': vocab_name}
        vocab = toolkit.get_action('vocabulary_create')(context, data)
        for tag in tags:
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            toolkit.get_action('tag_create')(context, data)
        return vocab



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