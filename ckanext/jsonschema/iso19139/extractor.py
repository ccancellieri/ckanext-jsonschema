import uuid

import ckan.lib.helpers as h
import ckan.lib.munge as munge
import ckanext.jsonschema.logic.get as _g
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.validators as _v
import six

def _extract_id(body):
    return body.get('fileIdentifier')


def _extract_from_iso(body, type, opt, version, data, errors, context):
    # if key==('name',):

    try:
        _extract_iso_name(body, type, opt, version, data, errors, context)
    except Exception as e:
        _v.stop_with_error('Error decoding metadata identification: {}'.format(str(e)), 'metadata identifier', errors)
    
    try:
        _extract_iso_data_identification(body, type, opt, version, data, errors, context)
    except Exception as e:
        _v.stop_with_error('Error decoding data identification: {}'.format(str(e)), 'data identification', errors)
    # TODO

    return body, type, opt, version, data



def _extract_iso_data_identification(body, type, opt, version, _data, errors, context):
    # _data = df.unflatten(data)

    data_identification = body.get('dataIdentification')
    if data_identification:
        citation = data_identification.get('citation')
        if citation:
            # TODO creation time, period, etc
            title = citation.get('title')
            if title:
                _data['title'] = title

        abstract = data_identification.get('abstract')
        if abstract:
            _data['notes'] = render_notes(body, type, opt, version, _data) or abstract

        _data['tags'] = []
        descriptive_keywords = data_identification.get('descriptiveKeywords')
        if descriptive_keywords:
            for dk in descriptive_keywords:

                keywords = dk.get('keywords')
                
                if keywords:
                    for k in keywords:
                        _data['tags'].append({'name': munge.munge_tag(k)})

        resourceConstraints = data_identification.get('resourceConstraints')
        if resourceConstraints:
            # In the case of an import, the license will be in _data['license_id'] and we don't want to overwrite that
            # with that coming from the source, which will be None because iso doesn't have license
            # In the case of an edit, there will be a license, and we store that in CKAN         
            license = resourceConstraints.get('license_id')
            if license:
                _data['license_id'] = license

            # We also have to set the license in the body extra
            body['dataIdentification']['resourceConstraints']['license_id'] = _data['license_id']


def _extract_iso_name(body, type, opt, version, data, errors, context):
    
    # TODO generate if still none...
    # munge title to package name
    # For taking a title of a package and munging it to a readable and valid dataset id. Symbols and whitespeace are converted into dashes, with multiple dashes collapsed. Ensures that long titles with a year at the end preserves the year should it need to be shortened. Example:

    # /api/util/dataset/munge_title_to_name?title=police:%20spending%20figures%202009
    
    name = body.get('fileIdentifier')

    if not name:
        name = str(uuid.uuid4())
    else:
        name = munge.munge_name(name)

    # if we are here we are creating/updating a metadata without file identifier
    # let's port back to body the new identifier ...
    body['fileIdentifier'] = name

    # should check CKAN version 
    if six.PY3:
        controller = 'dataset'
    else:
        controller = 'package'


    _dict = {
        'name': name,
        'url': h.url_for(controller = controller, action = 'read', id = name, _external = True),
    }
    data.update(_dict)




######################################################
## RESOURCES
######################################################

def _extract_iso_online_resource(body, type, opt, version, data, errors, context):
    
    _dict = dict(data)

    # name = munge.munge_filename(body.get('name'),'')
    name = body.get('name','Online resource')
    # if not name:
    #     name = 'Online resource'
    # if not name:
    #     _v.stop_with_error('Unable to obtain {}'.format(key), errors)
    
    description = body.get('description')
    _dict.update({
        'name': name,
        'description': description,
    })
    format = get_format(body.get('protocol',''), data.get('url',''))
    if format:
        _dict.update({
            'format': get_format(body.get('protocol',''), data.get('url',''))
        })

    return body, type, opt, version, _dict


def _extract_iso_resource_responsible(body, type, opt, version, data, errors, context):

    name = body.get('individualName', 'Contact')
    # as discussed on 06/12/2022
    organisationName = body.get('organisationName', name) or \
            _t.get_nested(body, ('onlineResource','name',))
    
    role = body.get('role','')
    # if not role:
    #     _v.stop_with_error('Unable to obtain role', 'role', errors)

    _dict = {
        'name': organisationName,
        'description': '{}: {}'.format(role, name)
    }
    data.update(_dict)

    return body, type, opt, version, data



def _extract_iso_graphic_overview(body, type, opt, version, data, errors, context):

    name = body.get('name', 'Graphic overview')
    
    description = body.get('description')
    _dict = {
        'name': name,
        'description': description,
    } 
    format = get_format(body.get('protocol',''), data.get('url',''))
    if format:
        _dict.update({
            'format': format
        })
    
    data.update(_dict)

    return body, type, opt, version, data


def render_notes(body, type, opt, version, data):
    
    import ckan.lib.base as base

    pkg = _g.get_pkg(body.get('fileIdentifier'))
    # ############actually it's a markdown...
    if pkg:
        try:
            return base.render('iso/description.html', extra_vars={'dataset': pkg })
        except Exception as e:
            # if e:
            #     message = 'Error on: {} line: {} Message:{}'.format(e.get('name',''),e.get('lineno',''),e.get('message',''))
            #     log.error(message)
            raise e



def get_format(protocol = None, url = None):
    
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
            'pdf': 'pdf',
            'png': 'png',
        }

        import os
        splitted_url = os.path.splitext(url)
        if len(splitted_url) > 1:
            extension = splitted_url[1][1:]
            if extension:
                return file_types.get(extension)
    
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
        'www:download-1.0-ftp--download':'ftp', # file for download through ftp
        'www:download-1.0-http--download':'http', # file for download
        #'file:geo':'', # gis file
        #'file:raster':'', # gis raster file
        'www:link-1.0-http--ical':'ical', # icalendar (url)
        'www:link-1.0-http--link':'http', # web address (url)
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
