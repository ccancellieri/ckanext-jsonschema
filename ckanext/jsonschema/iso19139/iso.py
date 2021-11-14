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

config = toolkit.config

TYPE_ISO='iso'
TYPE_ISO_ONLINE_RESOURCE='online-resource'
TYPE_ISO_RESOURCE_DATASET='resource-dataset'

SUPPORTED_DATASET_FORMATS = [TYPE_ISO]

SUPPORTED_ISO_RESOURCE_FORMATS = [TYPE_ISO_ONLINE_RESOURCE,TYPE_ISO_RESOURCE_DATASET]

# ISO_OPT={}

class JsonschemaIso(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(_i.IBinder, inherit = True)

    # IConfigurer

    def update_config(self, config_):
        pass
        #TODO

    # IBinder

    # def opt_map(self, dataset_type, opt, version):
    #     ''''
    #     returns a map of options (by type)
    #     '''
    #     opt.update({TYPE_ISO : ISO_OPT })
    #     return opt

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
            self._extract_from_online_resource(body, type, opt, version, key, data, errors, context)
            return
        elif type == TYPE_ISO_RESOURCE_DATASET:
            self._extract_from_resource_dataset(body, type, opt, version, key, data, errors, context)
            return
        
    def _extract_from_iso(self, body, type, opt, version, key, data, errors, context):
        # if key==('name',):
        _data = df.unflatten(data)

        _extract_iso_name(body, type, opt, version, key, _data, errors, context)
        
        # TODO

        data.update(df.flatten_dict(_data))


    def _extract_from_online_resource(self, body, type, opt, version, key, data, errors, context):
        # _data = df.unflatten(data)
        _extract_iso_online_resource_name(body, type, opt, version, key, data, errors, context)
        # TODO
        # data.update(df.flatten_dict(_data))

    def _extract_from_resource_dataset(self, body, type, opt, version, key, data, errors, context):
        # _data = df.unflatten(data)
        _extract_iso_resource_dataset_name(body, type, opt, version, key, data, errors, context)
        # TODO
        # data.update(df.flatten_dict(_data))


import ckan.lib.navl.dictization_functions as df
import uuid
def _extract_iso_name(body, opt, type, version, key, data, errors, context):

    # TODO generate if still none...
   
    # name = str(uuid.UUID(body.get('fileIdentifier')))
    name = str(body.get('fileIdentifier',uuid.uuid4()))
    name = name or data.get('name') #TODO error if null...

    if not name:
        _v.stop_with_error('Unable to obtain {}'.format(key), key, errors)
        
    _dict = {
        'name': name,
        'url': h.url_for(controller = 'package', action = 'read', id = name, _external = True),
    }
    data.update(_dict)

def _extract_iso_online_resource_name(body, opt, type, version, key, data, errors, context):
    # TODO
    name = str(body.get('name',uuid.uuid4()))
    name = name or data.get('name') #TODO error if null...

    if not name:
        _v.stop_with_error('Unable to obtain {}'.format(key), key, errors)
        
    _dict = {
        'name': name
    }
    data.update(_dict)

def _extract_iso_resource_dataset_name(body, opt, type, version, key, data, errors, context):

    name = str(body.get('name',uuid.uuid4()))
    name = name or data.get('name') #TODO error if null...

    if not name:
        _v.stop_with_error('Unable to obtain {}'.format(key), key, errors)
        
    _dict = {
        'name': name
    }
    data.update(_dict)







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