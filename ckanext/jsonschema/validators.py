
from sqlalchemy.sql.expression import true
from ckan.migration import versions

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
from ckan.plugins import PluginImplementations

import logging
log = logging.getLogger(__name__)


#############################################

import jsonschema
from jsonschema import validate,RefResolver,Draft4Validator,Draft7Validator
import json
import ckan.model as model

_SCHEMA_RESOLVER = jsonschema.RefResolver(base_uri='file://{}/'.format(_c.PATH_SCHEMA), referrer=None)

JSONSCHEMA_PLUGINS = PluginImplementations(_i.IBinder)

def schema_check(key, data, errors, context):
    '''
    Validator providing schema check capabilities
    '''
    extra = _t.resolve_extras(df.unflatten(data), True)

    body = extra.get(_c.SCHEMA_BODY_KEY)

    type = extra.get(_c.SCHEMA_TYPE_KEY)

    if not type:
        stop_with_error('Unable to load a valid json schema type', key, errors)

    schema = _t.get_schema_of(type)

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
        #TODO better message based on KEY mapping from IBinder plugin
        stop_with_error('Error validating: {}'.format(str(e)), key, errors)
    except Exception as e:
        #DEBUG
        #import traceback
        #traceback.print_exc()
        #TODO better message
        stop_with_error('Error validating: {}'.format(str(e)), key, errors)

def resource_extractor(key, data, errors, context):
    _data = df.unflatten(data)

    dataset_type = _data['type']
    resources = _data.get('resources')
    if not resources:
        return
    
    for resource in resources:
        extra = _t.resolve_resource_extras(dataset_type, resource, True)

        type = extra.get(_c.SCHEMA_TYPE_KEY)
        opt = extra.get(_c.SCHEMA_OPT_KEY, _c.SCHEMA_OPT)
        version = extra.get(_c.SCHEMA_VERSION_KEY, _c.SCHEMA_VERSION)

        for plugin in JSONSCHEMA_PLUGINS:
            
            if type in plugin.supported_resource_types(dataset_type, opt, version):
                try:
                    
                    body = extra.get(_c.SCHEMA_BODY_KEY)

                    # resource.get('__extras')
                    body, type, opt, version, _r = plugin.extract_from_json(body, type, opt, version, resource, errors, context)

                except Exception as e:
                    stop_with_error(str(e),key,errors)

                    # log.error('Error extracting resource type {}\
                    #     from body:\n{}\nError:\n{}'.format(type,body,str(e)))
                    # message = str(e)
                    # log.error(message)
                    # # e.error_summary = json.dumps(message)
                    # raise ValidationError(message)
                else:
                    # port back changes from body (and other extras) to the data model
                    _t.update_resource_extras(_r, body, type, opt, version)
                    # persist changes to the data model
                    resource.update(_r)

    data.update(df.flatten_dict(_data))

def before_extractor(key, data, errors, context):

    _data = df.unflatten(data)

    extra = _t.resolve_extras(_data, True)

    body = extra.get(_c.SCHEMA_BODY_KEY)

    type = extra.get(_c.SCHEMA_TYPE_KEY)

    opt = extra.get(_c.SCHEMA_OPT_KEY, _c.SCHEMA_OPT)

    version = extra.get(_c.SCHEMA_VERSION_KEY, _c.SCHEMA_VERSION)
    
    for plugin in JSONSCHEMA_PLUGINS:
        try:
            if type in plugin.supported_dataset_types(opt, version):
                body, type, opt, version, __data = plugin.before_extractor(body, type, opt, version, _data, errors, context)
                 # port back changes from body (and other extras) to the data model
                _t.update_extras(__data, body, type, opt, version)
                # update datamodel
                data.update(df.flatten_dict(__data))
        except Exception as e:
            stop_with_error(str(e),key,errors)

   

def extractor(key, data, errors, context):

    _data = df.unflatten(data)

    extra = _t.resolve_extras(_data, True)

    body = extra.get(_c.SCHEMA_BODY_KEY)

    type = extra.get(_c.SCHEMA_TYPE_KEY)

    opt = extra.get(_c.SCHEMA_OPT_KEY, _c.SCHEMA_OPT)

    version = extra.get(_c.SCHEMA_VERSION_KEY, _c.SCHEMA_VERSION)
    
    for plugin in JSONSCHEMA_PLUGINS:
        try:
            if type in plugin.supported_dataset_types(opt, version):
                body, type, opt, version, __data = plugin.extract_from_json(body, type, opt, version, _data, errors, context)
                # port back changes from body (and other extras) to the data model
                _t.update_extras(__data, body, type, opt, version)
                # update datamodel
                data.update(df.flatten_dict(_data))
        except Exception as e:
            stop_with_error(str(e),key,errors)











########### UNUSED

def _default_version(key, data, errors, context):
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

