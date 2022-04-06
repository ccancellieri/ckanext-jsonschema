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

    body = _t.as_dict(_t.get_package_body(_data))
    jsonschema_type = _t.get_package_type(_data)
    opt = _t.as_dict(_t.get_package_opt(_data))


    ######################### TODO #########################
    if opt.get('validation') == False:
        return

    if not jsonschema_type:
        stop_with_error('Unable to load a valid json schema type', key, errors)

    schema = _t.get_schema_of(jsonschema_type)

    if not schema:
        stop_with_error('Unable to load a valid json-schema for type {}'.format(jsonschema_type), key, errors)

    is_error = _t.draft_validation(jsonschema_type, body, errors)

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

def resources_extractor(key, data, errors, context):
    
    _data = df.unflatten(data)

    package_type = _t.get_package_type(_data)
    resources = _data.get('resources')

    if not resources:
        return
    
    try:
        for resource in resources:   
            resource_extractor(resource, package_type, errors, context)
        data.update(df.flatten_dict(_data))

    except df.StopOnError:
        raise
    except Exception as e:
        stop_with_error(str(e),key,errors)



def resource_extractor(resource, package_type, errors, context):

    body = _t.as_dict(_t.get_resource_body(resource))
    resource_type = _t.get_resource_type(resource)
    opt = _t.as_dict(_t.get_resource_opt(resource))

    # TODO This needs to account for the two different forms that resources can have: with __extras or flatten
    #jsonschema_extras = remove_jsonschema_extras_from_resource_data(resource)

    if resource_type not in configuration.get_supported_resource_types(package_type):
        return          

    plugin = configuration.get_plugin(package_type, resource_type)
    
    resource.update({
        _c.SCHEMA_BODY_KEY: body,
        _c.SCHEMA_TYPE_KEY :  resource_type,
        _c.SCHEMA_OPT_KEY :  opt,
    })

    extractor = plugin.get_resource_extractor(package_type, resource_type, context)
    extractor(resource, errors, context)

    resource.update({
        _c.SCHEMA_BODY_KEY: _t.as_json(_t.get_resource_body(resource)),
        _c.SCHEMA_TYPE_KEY :  _t.get_resource_type(resource),
        _c.SCHEMA_OPT_KEY : _t.as_json(_t.get_resource_opt(resource))
    })


def before_extractor(key, data, errors, context):

    _data = df.unflatten(data)

    jsonschema_type = _t.get_package_type(_data)
    opt = _t.get_package_opt(_data)

    ######################### TODO #########################
    opt.update({'validation': True})
  

    if jsonschema_type not in configuration.get_input_types():
        return
    
    plugin = configuration.get_plugin(jsonschema_type)

    try:
        extractor = plugin.get_before_extractor(jsonschema_type, context) 
        extractor(_data, errors, context)        
                
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

    package_type = _t.get_package_type(_data)

    if package_type not in configuration.get_supported_types():
        return

    plugin = configuration.get_plugin(package_type)

    try:
        extractor = plugin.get_package_extractor(package_type, _data, context)
        extractor(_data, errors, context)

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

    body = _t.as_dict(_t.get_package_body(_data))
    jsonschema_type = _t.get_package_type(_data)
    
    context = {}
    errors = []
    
    plugin = configuration.get_plugin(jsonschema_type)
    dump_to_output = plugin.get_dump_to_output(jsonschema_type)
    body = dump_to_output(_data, errors, context, format)

    return body


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



################# CKAN SCHEMA #####################


from ckan.logic.converters import convert_to_json_if_string

get_validator = toolkit.get_validator
convert_to_extras = toolkit.get_converter('convert_to_extras')
convert_from_extras = toolkit.get_converter('convert_from_extras')
not_missing = get_validator('not_missing')
not_empty = get_validator('not_empty')
resource_id_exists = get_validator('resource_id_exists')
package_id_exists = get_validator('package_id_exists')
ignore_missing = get_validator('ignore_missing')
empty = get_validator('empty')
boolean_validator = get_validator('boolean_validator')
int_validator = get_validator('int_validator')
OneOf = get_validator('OneOf')
isodate = get_validator('isodate')




def modify_package_schema(schema):

    schema[_c.SCHEMA_TYPE_KEY] = [convert_to_extras]
    schema[_c.SCHEMA_BODY_KEY] = [convert_to_extras]
    schema[_c.SCHEMA_OPT_KEY] = [convert_to_extras]

    schema['resources'].update({
        _c.SCHEMA_TYPE_KEY: [ignore_missing],
        _c.SCHEMA_BODY_KEY : [ignore_missing],
        _c.SCHEMA_OPT_KEY : [ignore_missing]
    })

    before = schema.get('__before')
    if not before:
        before = []
        schema['__before'] = before

    #TODO
    #Remove resource_extractor. Should be done with actions chain handler (resource_create, resource_update)
    
    # insert in front
    before.insert(0, jsonschema_fields_to_string)
    before.insert(0, resources_extractor)
    before.insert(0, extractor)
    before.insert(0, before_extractor)
    
    #the following will be the first...
    before.insert(0, schema_check)
    before.insert(0, jsonschema_fields_to_json)

    return schema

def show_package_schema(schema):
    
    schema[_c.SCHEMA_TYPE_KEY] = [convert_from_extras]
    schema[_c.SCHEMA_BODY_KEY] = [convert_from_extras, convert_to_json_if_string]
    schema[_c.SCHEMA_OPT_KEY] = [convert_from_extras, convert_to_json_if_string]

    schema['resources'].update({
        _c.SCHEMA_BODY_KEY : [ignore_missing, convert_to_json_if_string],
        _c.SCHEMA_OPT_KEY : [ignore_missing, convert_to_json_if_string]
    })

    return schema


def jsonschema_fields_to_json(key, data, errors, context):
    
    _data = df.unflatten(data)

    _data[_c.SCHEMA_BODY_KEY] = _t.as_dict(_t.get_package_body(_data))
    _data[_c.SCHEMA_TYPE_KEY] = _t.get_package_type(_data)
    _data[_c.SCHEMA_OPT_KEY] = _t.as_dict(_t.get_package_opt(_data))

    # for resource in _data.get('resources', []):
    #     jsonschema_resource_fields_to_json(resource)
    
    data.update(df.flatten_dict(_data))


def jsonschema_fields_to_string(key, data, errors, context):
    
    _data = df.unflatten(data)

    _data[_c.SCHEMA_BODY_KEY] = json.dumps(_t.as_dict(_t.get_package_body(_data)))
    _data[_c.SCHEMA_TYPE_KEY] = _t.get_package_type(_data)
    _data[_c.SCHEMA_OPT_KEY] = json.dumps(_t.as_dict(_t.get_package_opt(_data)))

    # for resource in _data.get('resources', []):
    #     jsonschema_resource_fields_to_string(resource)

    data.update(df.flatten_dict(_data))

def jsonschema_resource_fields_to_json(resource):

        jsonschema_type = _t.get_resource_type(resource)

        if jsonschema_type:
            
            body = _t.as_dict(_t.get_resource_body(resource))
            opt = _t.as_dict(_t.get_resource_opt(resource))

            #_t.set_resource_type(resource, jsonschema_type)
            _t.set_resource_body(resource, body)
            _t.set_resource_opt(resource, opt)

def jsonschema_resource_fields_to_string(resource):

        jsonschema_type = _t.get_resource_type(resource)

        if jsonschema_type:

            body = _t.as_json(_t.get_resource_body(resource))
            opt = _t.as_json(_t.get_resource_opt(resource))

            #_t.set_resource_type(resource, jsonschema_type)
            _t.set_resource_body(resource, body)
            _t.set_resource_opt(resource, opt)


############################################
