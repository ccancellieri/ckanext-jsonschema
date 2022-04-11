import logging
import traceback

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
    ######################### #### #########################

    item_validation(jsonschema_type, body, opt, key, errors, context)

    # TODO check if the following commented snippet could be necessary during package_create
    # hope we can leverage on resource_create chained action
    #
    # for resource in _data.get('resources',[]):
    #     jsonschema_type = _t.get_resource_type(resource)

    #     if not jsonschema_type:
    #         continue;

    #     body = _t.as_dict(_t.get_resource_body(resource))
    #     opt = _t.as_dict(_t.get_resource_opt(resource))

    #     ######################### TODO #########################
    #     if opt.get('validation') == False:
    #         return
    #     ######################### #### #########################

    #     item_validation(jsonschema_type, body, opt, key, errors, context)


def item_validation(jsonschema_type, jsonschema_body, jsonschema_opt, key, errors, context):
    if not jsonschema_type:
        stop_with_error('Unable to load a valid json schema type', key, errors)

    registry_entry = _t.get_from_registry(jsonschema_type)
    if not registry_entry:
        stop_with_error('Unable to find a valid entry into the registry for type {}'.format(jsonschema_type), key, errors)

    # BODY validation
    filename = registry_entry.get(_c.JSON_SCHEMA_KEY)
    if not filename:
        stop_with_error('Unable to find a valid json-schema file for type {}'.format(jsonschema_type), key, errors)

    schema = _t.get_schema_of(filename)
    if not schema:
        stop_with_error('Unable to load a valid json-schema for type {}'.format(jsonschema_type), key, errors)

    is_error = _t._draft_validation(filename, schema, jsonschema_body, errors)
    
    if is_error:
        stop_with_error('Unable to continue validation error found in Body for format {}'.format(jsonschema_type), key, errors)

    # OPT validation (optional, enabled if present in registry)
    filename = registry_entry.get(_c.JSON_OPT_SCHEMA_KEY)
    if filename:
        schema = _t.get_schema_of(filename)
        if not schema:
            stop_with_error('Unable to load a valid json-schema for type {}'.format(jsonschema_type), key, errors)
        
        is_error = _t._draft_validation(filename, schema, jsonschema_opt, errors)
        if is_error:
            stop_with_error('Unable to continue validation error found in <b>Options</b> for format {}'.format(jsonschema_type), key, errors)

def view_schema_check(key, data, errors, context):

    _data = df.unflatten(data)

    body, jsonschema_type, opt = get_extras_from_view(_data)
    
    if not jsonschema_type:
        stop_with_error('Unable to load a valid json schema type', key, errors)

    schema = _t.get_schema_of(jsonschema_type)

    if not schema:
        stop_with_error('Unable to load a valid json-schema for type {}'.format(jsonschema_type), key, errors)

    is_error = _t.draft_validation(jsonschema_type, body, errors)

    if is_error:
        stop_with_error('Unable to continue validation error found in View for format {}'.format(jsonschema_type), key, errors)

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
    
    _t.set_resource_body(resource, body)
    _t.set_resource_type(resource, resource_type)
    _t.set_resource_opt(resource, opt)


    extractor = plugin.get_resource_extractor(package_type, resource_type, context)
    extractor(resource, errors, context)

    # we set objects back to the dict
    # note: we do not reuse reference object, an extractor may have replaced some of them
    _t.set_resource_body(resource, _t.as_json(_t.get_resource_body(resource)))
    _t.set_resource_type(resource, _t.get_resource_type(resource))
    _t.set_resource_opt(resource, _t.as_json(_t.get_resource_opt(resource)))

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
ignore = get_validator('ignore')
json_object = get_validator('json_object')
empty = get_validator('empty')
boolean_validator = get_validator('boolean_validator')
int_validator = get_validator('int_validator')
OneOf = get_validator('OneOf')
isodate = get_validator('isodate')

def modify_package_schema(schema):

    schema[_c.SCHEMA_TYPE_KEY] = [convert_to_extras]
    schema[_c.SCHEMA_BODY_KEY] = [convert_to_extras]
    schema[_c.SCHEMA_OPT_KEY] = [convert_to_extras]

    # REF TO ISSUE: https://github.com/ckan/ckan/issues/4989
    # Arrays get flattened and make the jsonschema_body to be put in junk (see also issue)
    # Given a body composed of an array, like [{'connector': ...}], it is wrongly flattened as follow
    # ('resource', 0, 'jsonoschema_body', 0, 'connector',)
    # instead of limiting the scope to the schema
    # ('resource', 0, 'jsonoschema_body',)
    # So we need to enforce the jsonschema_body and the jsonschema_opt to be an object.

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
    before.insert(0, schema_check)
    before.insert(0, jsonschema_fields_should_be_objects) #https://github.com/ckan/ckan/issues/4989
    #the following will be the first...
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

def jsonschema_fields_should_be_objects(key, data, errors, context):
    '''
    This function checks that jsonschema_body and jsonschema_opt are present and are objects both in the package and in every resource
    If the check fails, it returns a validation error
    '''

    unflattened_data = df.unflatten(data)

    package_body = _t.get_package_body(unflattened_data)
    package_opt = _t.get_package_opt(unflattened_data)


    try:
        json_object(package_body)
        json_object(package_opt)
    except (ValueError, TypeError):
        traceback.print_exc()
        message = 'Package body and opt should be an object. Array is not allowed to be used at root level.'
        stop_with_error(str(_(message)),key,errors)
    
    else:

        for resource in unflattened_data.get('resources',[]):

            # skip this validation if it is not a jsonschema resource
            if not _t.get_resource_type(resource):
                continue

            resource_body = _t.get_resource_body(resource)
            resource_opt = _t.get_resource_opt(resource)

            try:
                # When creating a new resource, the body and the opts come as strings instead of dicts,
                # so we first need to load them
                if isinstance (resource_body, str):
                    resource_body = json.loads(resource_body)
                if isinstance (resource_opt, str):
                    resource_opt = json.loads(resource_opt)

                json_object(resource_body)
                json_object(resource_opt)

            except (ValueError, TypeError):
                traceback.print_exc()
                resource_position = resource.get('position') or 'unknown'
                resource_name = resource.get('name') or 'unnamed'
                message = 'Resource body and opt should be an object. Please check resource n.{} named: "{}"'.format(resource_position, resource_name)
                message += '   AArray is not allowed to be used at root level.'
                stop_with_error(str(_(message)), key, errors)
                
############################################