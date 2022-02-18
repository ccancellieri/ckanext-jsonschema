
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

    log.error('Stopped with error: {}'.format(message))
    log.error('on key: {}'.format(key))
    log.error('Errors: {}'.format(str(errors)))

    tuple_key = (key,)
    if not tuple_key in errors:
        errors[tuple_key] = []
    
    errors[tuple_key].append(_(message))
    
    raise StopOnError(_(message))

import ckanext.jsonschema.constants as _c

import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.interfaces as _i
from ckan.plugins import PluginImplementations

import logging
log = logging.getLogger(__name__)


#############################################

import jsonschema
from jsonschema import Draft7Validator
import json

# TODO move me to tools
_SCHEMA_RESOLVER = jsonschema.RefResolver(base_uri='file://{}/'.format(_c.PATH_SCHEMA), referrer=None)

# TODO move me and relatives to plugin.pu
JSONSCHEMA_PLUGINS = PluginImplementations(_i.IBinder)

# TODO create validation in tools then call it from here.
# TODO better message in case of validation Error (once in tools)
def schema_check(key, data, errors, context):
    '''
    Validator providing schema check capabilities
    '''
    _data = df.unflatten(data)
    
    body, type, _, _ = get_extras_from_data(_data)

    if not type:
        stop_with_error('Unable to load a valid json schema type', key, errors)

    schema = _t.get_schema_of(type)

    if not schema:
        stop_with_error('Unable to load a valid json-schema for type {}'.format(type), key, errors)


    validator = Draft7Validator(schema, resolver=_SCHEMA_RESOLVER)

    # For each error, build the error message for the frontend with the path and the message
    is_error = False

    for idx, error in enumerate(sorted(validator.iter_errors(body), key=str)):
        
        is_error = True

        error_path = 'metadata'

        for path in error.absolute_path:
            if isinstance(path, int):
                translated = _(', at element n.')
                error_path = ('{} {} {}').format(error_path, translated, path + 1)
            else:
                error_path = ('{} -> {}').format(error_path, path)
            

        errors[('validation_error_' + str(idx), idx, 'path',)] = [error_path]
        errors[('validation_error_' + str(idx), idx, 'message',)] = [error.message]

        log.error('Stopped with error')
        log.error('Path: {}'.format(error_path))
        log.error('Message: {}'.format(error.message))

    if is_error:
        raise StopOnError()


def resource_extractor(key, data, errors, context):
    _data = df.unflatten(data)

    dataset_type = _data['type']
    resources = _data.get('resources')
    if not resources:
        return
    
    for resource in resources:
        
        body, type, opt, version = get_extras_from_resource(resource)

        context.update({
            _c.SCHEMA_BODY_KEY: body,
            _c.SCHEMA_TYPE_KEY : type,
            _c.SCHEMA_OPT_KEY : opt,
            _c.SCHEMA_VERSION_KEY : version
        })

        #jsonschema_extras = remove_jsonschema_extras_from_resource_data(resource)

        for plugin in JSONSCHEMA_PLUGINS:
            
            if type in plugin.supported_resource_types(dataset_type, opt, version):
                try:
                    
                    plugin.extract_from_json(resource, errors, context)
                
                except df.StopOnError:
                    raise
                except Exception as e:
                    stop_with_error(str(e),key,errors)

                else:
                    pass
                    #enrich_resource_data_with_jsonschema_extras(resource, jsonschema_extras)

                    # port back changes from body (and other extras) to the data model
                    #_t.update_resource_extras(_r, body, type, opt, version)
                    #_t.update_extras_from_resource_context(resource, context)
                    # persist changes to the data model
                    # resource.update(_r)

    data.update(df.flatten_dict(_data))

def before_extractor(key, data, errors, context):

    _data = df.unflatten(data)

    body, type, opt, version = get_extras_from_data(_data)

    context.update({
        _c.SCHEMA_BODY_KEY: body,
        _c.SCHEMA_TYPE_KEY : type,
        _c.SCHEMA_OPT_KEY : opt,
        _c.SCHEMA_VERSION_KEY : version
    })

    for plugin in JSONSCHEMA_PLUGINS:
        try:
            if type in plugin.supported_input_types(opt, version):
                
                plugin.before_extractor(_data, errors, context)
                 # port back changes from body (and other extras) to the data model
                
                _body = _t.get_context_body(context)
                _type = _t.get_context_type(context)
                _t.update_extras(_data, _body, _type, opt, version)
                # update datamodel
                data.update(df.flatten_dict(_data))
        except df.StopOnError:
            raise
        except Exception as e:
            import traceback
            traceback.print_exc()
            stop_with_error(str(e),key,errors)

   

def extractor(key, data, errors, context):

    _data = df.unflatten(data)

    body, type, opt, version = get_extras_from_data(_data)

    context.update({
        _c.SCHEMA_BODY_KEY: body,
        _c.SCHEMA_TYPE_KEY : type,
        _c.SCHEMA_OPT_KEY : opt,
        _c.SCHEMA_VERSION_KEY : version
    })
    
    jsonschema_extras = remove_jsonschema_extras_from_package_data(_data)

    for plugin in JSONSCHEMA_PLUGINS:
        try:
            if type in plugin.supported_dataset_types(opt, version):
                
                plugin.extract_from_json(_data, errors, context)

                enrich_package_data_with_jsonschema_extras(_data, jsonschema_extras)

                # port back changes from body (and other extras) to the data model
                _t.update_extras_from_context(_data, context)

                # update datamodel
                data.update(df.flatten_dict(_data))
                
        except df.StopOnError:
            raise
        except Exception as e:
            stop_with_error(str(e),key,errors)


# TODO PACKAGE_SHOW ??
def dataset_dump(dataset_id, format = None):

    _data = _t.get(dataset_id)

    if format == None:
        return _data

    body, type, opt, version = get_extras_from_data(_data)

    for plugin in JSONSCHEMA_PLUGINS:
        if type in plugin.supported_output_types(type, opt, version):
                   
            context = {}
            # resource.get('__extras')
            body = plugin.dump_to_output(body, type, opt, version, _data, format, context)
            # port back changes from body (and other extras) to the data model
            return body


def get_extras_from_resource(resource):
    
    body = _t.as_dict(_t.get_resource_body(resource))
    type = _t.get_resource_type(resource)
    opt = _t.as_dict(_t.get_resource_opt(resource))
    version = _t.as_dict(_t.get_resource_version(resource) or _c.SCHEMA_VERSION) #TODO

    return body, type, opt, version

def get_extras_from_data(data):
    
    body = _t.as_dict(_t.get_dataset_body(data))
    type = _t.get_dataset_type(data)
    opt = _t.as_dict(_t.get_dataset_opt(data))
    version = _t.as_dict(_t.get_dataset_version(data))

    return body, type, opt, version

def remove_jsonschema_extras_from_package_data(data):
    '''
    Clears data from jsonschema extras, so it seems like a clean CKAN package when passed into plugins
    Returns the removed extras as a tuple (index, extra) so that they can be put back into data

    '''

    jsonschema_extras = []
    filtered_extras = []

    keys = [_c.SCHEMA_BODY_KEY, _c.SCHEMA_TYPE_KEY, _c.SCHEMA_OPT_KEY, _c.SCHEMA_VERSION_KEY]

    for idx, extra in enumerate(data.get('extras')):
        if extra.get('key') in keys:
            jsonschema_extras.append((idx, extra))
        else:
            filtered_extras.append(extra)

    data['extras'] = filtered_extras     
    
    return jsonschema_extras

def remove_jsonschema_extras_from_resource_data(data):
    '''
    Clears data from jsonschema extras, so it seems like a clean CKAN package when passed into plugins
    Returns the removed extras as a tuple (index, extra) so that they can be put back into data
    '''

    jsonschema_extras = []
    filtered_extras = []

    keys = [_c.SCHEMA_BODY_KEY, _c.SCHEMA_TYPE_KEY, _c.SCHEMA_OPT_KEY, _c.SCHEMA_VERSION_KEY]

    for key in data.get('__extras'):

        value = data.get('__extras').get(key)

        if key in keys:
            jsonschema_extras.append({key: value})
        else:
            filtered_extras.append({key: value})

    data['__extras'] = filtered_extras     
    
    return jsonschema_extras

def enrich_package_data_with_jsonschema_extras(data, extras):

    for jsonschema_extra in extras:
        position, element = jsonschema_extra
        data['extras'].insert(position, element)

def enrich_resource_data_with_jsonschema_extras(data, extras):

    for jsonschema_extra in extras:
        data['__extras'].append(jsonschema_extra)

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
