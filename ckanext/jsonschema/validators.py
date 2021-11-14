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
    extra = resolve_extras(df.unflatten(data), True)

    body = extra.get(_c.SCHEMA_BODY_KEY)

    type = extra.get(_c.SCHEMA_TYPE_KEY)

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
        #TODO better message based on KEY mapping from IBinder plugin
        stop_with_error('Error validating: {}'.format(str(e)), key, errors)
    except Exception as e:
        #DEBUG
        #import traceback
        #traceback.print_exc()
        #TODO better message
        stop_with_error('Error validating:{}'.format(str(e)), key, errors)

def resource_extractor(key, data, errors, context):
    _data = df.unflatten(data)

    resources = _data.get('resources')

    if not resources:
        return

    for resource in resources:

        extra = resolve_resource_extras(_data['type'], resource, True)
        # resource.get('__extras')

        body = extra.get(_c.SCHEMA_BODY_KEY)

        type = extra.get(_c.SCHEMA_TYPE_KEY)

        opt = extra.get(_c.SCHEMA_OPT_KEY, _c.SCHEMA_OPT)

        version = extra.get(_c.SCHEMA_VERSION_KEY, _c.SCHEMA_VERSION)

        for plugin in JSONSCHEMA_PLUGINS:
            try:
                if type in plugin.supported_resource_types(_data['type'], opt, version):
                    plugin.extract_from_json(body, type, opt, version, key, resource, errors, context)
            except Exception as e:
                log.error('Error extracting dataset type {}\
                    from body:\n{}\nError:\n{}'.format(type,body,str(e)))

    data.update(df.flatten_dict(_data))

def extractor(key, data, errors, context):

    extra = resolve_extras(df.unflatten(data), True)

    body = extra.get(_c.SCHEMA_BODY_KEY)

    type = extra.get(_c.SCHEMA_TYPE_KEY)

    opt = extra.get(_c.SCHEMA_OPT_KEY, _c.SCHEMA_OPT)

    version = extra.get(_c.SCHEMA_VERSION_KEY, _c.SCHEMA_VERSION)
    
    for plugin in JSONSCHEMA_PLUGINS:
        try:
            if type in plugin.supported_dataset_types(opt, version):
                plugin.extract_from_json(body, type, opt, version, key, data, errors, context)
        except Exception as e:
            log.error('Error extracting dataset type {}\
                from body:\n{}\nError:\n{}'.format(type,body,str(e)))

def resolve_resource_extras(dataset_type, resource, as_dict = False):
    from ckanext.jsonschema.plugin import handled_resource_types
    # Pre-setting defaults
    resource_types = handled_resource_types(dataset_type)
    if resource_types:
        _type = resource_types[0]
        body = _t.get_template_of(_type)
    else:
        _type = None
        body = {}
    
    opt = _c.SCHEMA_OPT
    version = _c.SCHEMA_VERSION

    # Checking extra data content for extration
    e = resource.get('__extras',{})
    if not e:
        # edit existing resource
        e = resource

    body = e.get(_c.SCHEMA_BODY_KEY, body)
    _type = e.get(_c.SCHEMA_TYPE_KEY, _type)
    version = e.get(_c.SCHEMA_VERSION_KEY, version)
    opt = e.get(_c.SCHEMA_OPT_KEY, opt)
    
    # body = resource.get(_c.SCHEMA_BODY_KEY, body)
    # _type = resource.get(_c.SCHEMA_TYPE_KEY, _type)
    # version = resource.get(_c.SCHEMA_VERSION_KEY, version)
    # opt = resource.get(_c.SCHEMA_OPT_KEY, opt)
            
    if as_dict:
        if not isinstance(body, dict):
            body = json.loads(body)
        if not isinstance(opt, dict):
            try:
                opt = json.loads(opt)
            except Exception as e:
                log.error('Unable to properly deserialize \'opt\' it should be a json object...')
    else:
        if not isinstance(body, str):
            body = json.dumps(body)
        if not isinstance(opt, str):
            opt = json.dumps(opt)
    
    return {
        _c.SCHEMA_OPT_KEY : opt,
        _c.SCHEMA_BODY_KEY: body,
        _c.SCHEMA_TYPE_KEY: _type,
        _c.SCHEMA_VERSION_KEY: version
    }

def resolve_extras(data, as_dict = False):
    # Pre-setting defaults
    _type = get_dataset_type(data)
    body = _t.get_template_of(_type)
    opt = _c.SCHEMA_OPT
    version = _c.SCHEMA_VERSION

    # Checking extra data content for extration
    for e in data.get('extras',[]):
        key = e.get('key')
        if not key:
            raise Exception('Unable to resolve extras with an empty key')
        if key == _c.SCHEMA_BODY_KEY:
            body = e['value']
        elif key == _c.SCHEMA_TYPE_KEY:
            _type = e['value']
        elif key == _c.SCHEMA_VERSION_KEY:
            version = e['value']
        elif key == _c.SCHEMA_OPT_KEY:
            opt = e['value']
            
    if as_dict:
        if not isinstance(body, dict):
            body = json.loads(body)
        if not isinstance(opt, dict):
            opt = json.loads(opt)
    else:
        if not isinstance(body, str):
            body = json.dumps(body)
        if not isinstance(opt, str):
            opt = json.dumps(opt)
    
    return {
        _c.SCHEMA_OPT_KEY : opt,
        _c.SCHEMA_BODY_KEY: body,
        _c.SCHEMA_TYPE_KEY: _type,
        _c.SCHEMA_VERSION_KEY: version
    }


# TODO
def resource_serializer(key, data, errors, context):
    '''
    serialize to body the data model in the desired form
    '''
    extra = resolve_extras(df.unflatten(data), True)

    body = extra.get(_c.SCHEMA_BODY_KEY)

    type = extra.get(_c.SCHEMA_TYPE_KEY)

    opt = extra.get(_c.SCHEMA_OPT_KEY, _c.SCHEMA_OPT)

    version = extra.get(_c.SCHEMA_VERSION_KEY, _c.SCHEMA_VERSION)

    _serialize_with_plugin(body, type, opt, version, key, data, errors, context)

def serializer(key, data, errors, context):
    '''
    serialize to body the data model in the desired form
    '''
    extra = resolve_extras(df.unflatten(data), True)

    body = extra.get(_c.SCHEMA_BODY_KEY)

    type = extra.get(_c.SCHEMA_TYPE_KEY)

    opt = extra.get(_c.SCHEMA_OPT_KEY, _c.SCHEMA_OPT)

    version = extra.get(_c.SCHEMA_VERSION_KEY, _c.SCHEMA_VERSION)

    # if key[::2] == ('resources',_c.SCHEMA_BODY_KEY):
    #     # TODO we are into resources
    #    while data[key]

    _serialize_with_plugin(body, type, opt, version, key, data, errors, context)

# TODO SERIALIZER
def _serialize_with_plugin(body, type, opt, version, key, data, errors, context):
    for plugin in JSONSCHEMA_PLUGINS:
        try:
            if type in plugin.supported_dataset_types(opt, version):
                # TODO SERIALIZER INTERFACE
                plugin.extract_from_json(body, type, opt, version, key, data, errors, context)
        except Exception as e:
            log.error('Error extracting dataset type {}\
                from body:\n{}\nError:\n{}'.format(type,body,str(e)))


# TODO CKAN contribution
def get_dataset_type(data = None):
    
    _type = data and data.get('type')
    if _type:
        return _type

    from ckan.common import c
    # TODO: https://github.com/ckan/ckan/issues/6518
    path = c.environ['CKAN_CURRENT_URL']
    _type = path.split('/')[1]
    return _type









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

