import logging
import os

import ckan.plugins.toolkit as toolkit
import ckanext.jsonschema.configuration as configuration
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.view_tools as _vt

log = logging.getLogger(__name__)

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

    tuple_key = key
    if not isinstance(key, tuple):
        tuple_key = (key,)
        
    
    if not tuple_key in errors:
        errors[tuple_key] = []
    
    errors[tuple_key].append(_(message))
    
    raise StopOnError(_(message))



#############################################


import json


# TODO create validation in tools then call it from here.
# TODO better message in case of validation Error (once in tools)
def schema_check(key, data, errors, context):
    '''
    Validator providing schema check capabilities
    '''

    _data = df.unflatten(data)

    body, _type, opt = get_extras_from_data(_data)

    ######################### TODO #########################
    if opt.get('validation') == False:
        return

    if not _type:
        stop_with_error('Unable to load a valid json schema type', key, errors)

    schema = _t.get_schema_of(_type)

    if not schema:
        stop_with_error('Unable to load a valid json-schema for type {}'.format(_type), key, errors)

    is_error = _t.draft_validation(_type, body, errors)

    if is_error:
        raise StopOnError()

def view_schema_check(key, data, errors, context):

    _data = df.unflatten(data)

    body, _type, opt = get_extras_from_view(_data)
    
    if not _type:
        stop_with_error('Unable to load a valid json schema type', key, errors)

    schema = _t.get_schema_of(_type)

    if not schema:
        stop_with_error('Unable to load a valid json-schema for type {}'.format(_type), key, errors)

    is_error = _t.draft_validation(_type, body, errors)

    if is_error:
        raise StopOnError()

def resource_extractor(key, data, errors, context):
    _data = df.unflatten(data)

    dataset_type = _t.get_dataset_type(_data) # TODO should be jsonschema_type
    resources = _data.get('resources')
    if not resources:
        return
    
    for resource in resources:
        
        body, resource_type, opt = get_extras_from_resource(resource)

        # TODO This needs to account for the two different forms that resources can have: with __extras or flatten
        #jsonschema_extras = remove_jsonschema_extras_from_resource_data(resource)

        if resource_type not in configuration.get_supported_resource_types(dataset_type):
            return          

        plugin = configuration.get_plugin(dataset_type, resource_type)
        
        context.update({
            _c.SCHEMA_BODY_KEY: body,
            _c.SCHEMA_TYPE_KEY : resource_type,
            _c.SCHEMA_OPT_KEY : opt,
        })

        try:
            extractor = plugin.get_resource_extractor(dataset_type, resource_type, context)
            extractor(resource, errors, context)
            _t.update_extras_from_resource_context(resource, context)
            data.update(df.flatten_dict(_data))

        except df.StopOnError:
            raise
        except Exception as e:
            stop_with_error(str(e),key,errors)


def before_extractor(key, data, errors, context):

    _data = df.unflatten(data)

    body, _type, opt = get_extras_from_data(_data)

    ######################### TODO #########################
    opt.update({'validation': True})
     
    context.update({
        _c.SCHEMA_BODY_KEY: body,
        _c.SCHEMA_TYPE_KEY : _type,
        _c.SCHEMA_OPT_KEY : opt
    })

    if _type not in configuration.get_input_types():
        return
    
    plugin = configuration.get_plugin(_type)

    try:
        extractor = plugin.get_before_extractor(_type, context) 
        extractor(_data, errors, context)        

        _t.update_extras_from_context(_data, context)
                
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

    body, package_type, opt = get_extras_from_data(_data)

    
    #jsonschema_extras = _t.remove_jsonschema_extras_from_package_data(_data)

    if package_type not in configuration.get_supported_types():
        return

    plugin = configuration.get_plugin(package_type)

    # _data.update({
    #     _c.SCHEMA_BODY_KEY: body,
    #     _c.SCHEMA_TYPE_KEY : package_type,
    #     _c.SCHEMA_OPT_KEY : opt
    # })

    try:
        extractor = plugin.get_package_extractor(package_type, context)
        extractor(_data, errors, context)

        #_t.enrich_package_data_with_jsonschema_extras(_data, jsonschema_extras)

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

    body, package_type, opt = get_extras_from_data(_data)

    
    context = {
        _c.SCHEMA_BODY_KEY: body,
        _c.SCHEMA_TYPE_KEY : package_type,
        _c.SCHEMA_OPT_KEY : opt,
    }
    errors = []
    
    plugin = configuration.get_plugin(package_type)
    dump_to_output = plugin.get_dump_to_output(package_type)
    body = dump_to_output(_data, errors, context, format)

    return body


def get_extras_from_data(data):
    
    body = _t.as_dict(_t.get_dataset_body(data))
    type = _t.get_dataset_type(data)
    opt = _t.as_dict(_t.get_dataset_opt(data))

    return body, type, opt


def get_extras_from_resource(resource):
    
    body = _t.as_dict(_t.get_resource_body(resource))
    type = _t.get_resource_type(resource)
    opt = _t.as_dict(_t.get_resource_opt(resource))

    return body, type, opt


def get_extras_from_view(view):
    
    body = _t.as_dict(_vt.get_view_body(view))
    _type = _vt.get_view_type(view)
    opt = _t.as_dict(_vt.get_view_opt(view))

    return body, _type, opt

########### UNUSED


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


def jsonschema_fields_to_json(key, data, errors, context):
    
    _data = df.unflatten(data)
    
    body, jsonschema_type, opt = get_extras_from_data(_data)

    _data[_c.SCHEMA_BODY_KEY] = body
    _data[_c.SCHEMA_TYPE_KEY] = jsonschema_type
    _data[_c.SCHEMA_OPT_KEY] = opt

    data.update(df.flatten_dict(_data))

def jsonschema_fields_to_string(key, data, errors, context):
    
    _data = df.unflatten(data)

    body, jsonschema_type, opt = get_extras_from_data(_data)

    _data[_c.SCHEMA_BODY_KEY] = json.dumps(body)
    _data[_c.SCHEMA_TYPE_KEY] = jsonschema_type
    _data[_c.SCHEMA_OPT_KEY] = json.dumps(opt)

    data.update(df.flatten_dict(_data))