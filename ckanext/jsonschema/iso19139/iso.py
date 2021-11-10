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

TYPE_ISO='iso'

class JsonschemaIso(p.SingletonPlugin):
    p.implements(_i.IBinder)

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
    def bind_with(self, body, opt, type, version):
        if version != _c.SCHEMA_VERSION:
            # when version is not the default one we don't touch
            return False

        if type == TYPE_ISO:
            return True

    def extract_from_json(self, body, opt, type, version, key, data, errors, context):
        # TODO which type schema or dataset?
        
        if key==('name',):
            extract_name(body, opt, type, version, key, data, errors, context)
            


import ckan.lib.navl.dictization_functions as df

def extract_name(body, opt, type, version, key, data, errors, context):

    _data = df.unflatten(data)

    # name:
    #<gmd:MD_Metadata 
    #<gmd:fileIdentifier>
    #<gco:CharacterString>c26de669-90f9-43a1-ae4d-6b1b9660f5e0</gco:CharacterString>
    # TODO generate if still none...
    import uuid
    
    # name = str(uuid.UUID(body.get('fileIdentifier')))
    name = str(body.get('fileIdentifier',uuid.uuid4()))
    name = name or _data.get('name') #TODO error if null...

    if not name:
        _v.stop_with_error('Unable to obtain {}'.format(key), key, errors)
        
    _dict = {
        'name': name,
        'url': h.url_for(controller = 'package', action = 'read', id = name, _external = True),
    }
    data.update(df.flatten_dict(_dict))







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