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
# isodate

import ckan.lib.navl.dictization_functions as df

missing = df.missing
StopOnError = df.StopOnError
Invalid = df.Invalid

def stop_with_error(message, key, errors):
    errors[key].append(_(message))
    raise StopOnError(_(message))

import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.interfaces as _i

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

_SCHEMA_RESOLVER = jsonschema.RefResolver(base_uri='file://{}/'.format(_c.PATH_SCHEMA), referrer=None)

    
def default_version(key, data, errors, context):
    '''
    Validator providing default values 
    '''
    if not data[key]:
        data[key]=_c.SCHEMA_VERSION
    return

def _get_body(key, data, errors, context):
    body = data.get(key)
    if not body:
        stop_with_error(_('Can\'t validate empty Missing value {}'.format(key)), key, errors)

    # ##############SIDE EFFECT#################
    # # if configuration comes as string:
    # # convert incoming string to a dict
    try:
        if not isinstance(body, dict):
            body = json.loads(body)
    except Exception as e:
        stop_with_error('Not a valid json dict :{}'.format(str(e)), key, errors)
    # ##############SIDE EFFECT#################

    # TODO extension point (we may want to plug other schema checkers)
    if not body:
        stop_with_error('Unable to load a valid json schema body', key, errors)

    return body

def schema_check(key, data, errors, context):
    '''
    Validator providing schema check capabilities
    '''
    body = _get_body(key, data, errors, context)
    
    type = data.get((_c.SCHEMA_TYPE_KEY,))

    # TODO extension point (we may want to plug other schema checkers)
    if not type:
        stop_with_error('Unable to load a valid json schema type', key, errors)

    schema = _t.get_schema_of(type)

    # TODO extension point (we may want to plug other schema checkers)
    if not schema:
        stop_with_error('Unable to load a valid json-schema for type {}'.format(type), key, errors)

    try:
        # if not Draft4Validator.check_schema(constants.LAZY_GROUP_SCHEMA):
        #     raise Exception('schema not valid') #TODO do it once on startup (constants)
        #validator = Draft4Validator(constants.LAZY_GROUP_SCHEMA, resolver=resolver, format_checker=None)
        validator = Draft7Validator(schema, resolver=_SCHEMA_RESOLVER)
        # VALIDATE JSON SCHEMA
        _ret = validator.validate(body)

    except jsonschema.exceptions.ValidationError as e:
        #DEBUG
        #import traceback
        #traceback.print_exc()
        #TODO better message
        stop_with_error('Error validating: {}'.format(str(e)), key, errors)
    except Exception as e:
        #DEBUG
        #import traceback
        #traceback.print_exc()
        #TODO better message
        stop_with_error('Error validating:{}'.format(str(e)), key, errors)


def extractor(key, data, errors, context):

    body = _get_body(key, data, errors, context)

    type = data.get((_c.SCHEMA_TYPE_KEY,))

    opt = data.get((_c.SCHEMA_OPT_KEY,))

    version = data.get((_c.SCHEMA_VERSION_KEY,))

    from ckan.plugins import PluginImplementations
    # from ckan.plugins.interfaces import IConfigurable
    # for plugin in PluginImplementations(IConfigurable):
    for plugin in PluginImplementations(_i.IBinder):
        try:
            plugin.extract_from_json(body, opt, type, version, key, data, errors, context)
        except Exception as e:
            stop_with_error('Error extracting json model: {}'.format(str(e)), key, errors)

def serializer(key, data, errors, context):
    '''
    serialize to body the data model in the desired form
    '''

    body = _get_body(key, data, errors, context)

    type = data.get((_c.SCHEMA_TYPE_KEY,))

    opt = data.get((_c.SCHEMA_OPT_KEY,))

    version = data.get((_c.SCHEMA_VERSION_KEY,))

    from ckan.plugins import PluginImplementations
    # from ckan.plugins.interfaces import IConfigurable
    # for plugin in PluginImplementations(IConfigurable):
    for plugin in PluginImplementations(_i.IBinder):
        if plugin.bind_with(body, opt, type, version):
            plugin.extract_from_json(body, opt, type, version, key, data, errors, context)


