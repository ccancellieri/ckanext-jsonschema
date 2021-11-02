from sqlalchemy.sql.expression import true
import ckan.lib.helpers as h
import ckan.plugins.toolkit as toolkit

_get_or_bust= toolkit.get_or_bust
_ = toolkit._
# import ckan.logic.validators as v

not_empty = toolkit.get_validator('not_empty')
#ignore_missing = p.toolkit.get_validator('ignore_missing')
#ignore_empty = p.toolkit.get_validator('ignore_empty')
is_boolean = toolkit.get_validator('boolean_validator')
# https://docs.ckan.org/en/2.8/extensions/validators.html#ckan.logic.validators.json_object
# NOT FOUND import ckan.logic.validators.json_object
#json_object = p.toolkit.get_validator('json_object')

import ckan.lib.navl.dictization_functions as df

missing = df.missing
StopOnError = df.StopOnError
Invalid = df.Invalid

import ckanext.jsonschema.tools as tools
import ckanext.jsonschema.constants as constants
import ckanext.jsonschema.logic.get as get
# import ckanext.jsonschema.validators as v
import logging
log = logging.getLogger(__name__)

#TODO... something more ckan oriented? 
#https://github.com/ckan/ckan/blob/c5c529d10ebe63d8573515483fdd46e0839477f0/ckan/lib/dictization/model_dictize.py
def instance_to_dict(i):
    '''
    The Validator receive a resource instance, we need a dict...
    '''
    return i


#############################################

import jsonschema
from jsonschema import validate,RefResolver,Draft4Validator,Draft7Validator
import json
import ckan.model as model

_SCHEMA_RESOLVER = jsonschema.RefResolver(base_uri='file://{}/'.format(constants.PATH_SCHEMA), referrer=None)

def _stop_on_error(errors,key,message):
    errors[key].append(_(message))
    raise StopOnError(_(message))


def schema_check(key, data, errors, context):
    '''
    Validator providing schema check capabilities
    '''
    body = data.get(key)
    if not body:
        _stop_on_error(errors,key,_('Can\'t validate empty Missing value {}'.format(key)))

    ##############SIDE EFFECT#################
    # if configuration comes as string:
    # convert incoming string to a dict
    try:
        if not isinstance(body, dict):
            data[key] = json.loads(body)
    except Exception as e:
        _stop_on_error(errors,key,'Not a valid json dict :{}'.format(str(e)))
    ##############SIDE EFFECT#################

    jsonschema_type = data.get((constants.SCHEMA_TYPE_KEY,))
    if not jsonschema_type or jsonschema_type is missing:
        dataset = instance_to_dict(context['dataset'])

        try:
            jsonschema_type = tools.dataset_type(dataset)
        except Exception as e:
            _stop_on_error(errors,key,_('Missing default type value, please check available json-mapping formats {}'.format(str(e))))
        # jsonschema_type=data[(constants.SCHEMA_TYPE_KEY,)]
        
    # TODO extension point (we may want to plug other schema checkers)
    if not jsonschema_type:
        _stop_on_error(errors,key,'Unable to load a valid jsonschema_type')

    try:

        # if not Draft4Validator.check_schema(constants.LAZY_GROUP_SCHEMA):
        #     raise Exception('schema not valid') #TODO do it once on startup (constants)
        schema = tools.get_schema_of(jsonschema_type)
        #validator = Draft4Validator(constants.LAZY_GROUP_SCHEMA, resolver=resolver, format_checker=None)
        validator = Draft7Validator(schema, resolver=_SCHEMA_RESOLVER)
        # VALIDATE JSON SCHEMA
        _ret = validator.validate(config)

    except jsonschema.exceptions.ValidationError as e:
        #DEBUG
        #import traceback
        #traceback.print_exc()
        #TODO better message
        _stop_on_error(errors,key,'Error validating:{}'.format(str(e)))
    except Exception as e:
        #DEBUG
        #import traceback
        #traceback.print_exc()
        #TODO better message
        _stop_on_error(errors,key,'Error validating:{}'.format(str(e)))

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