import threading

import ckan.plugins.toolkit as toolkit

_ = toolkit._
import json
import logging

import ckanext.jsonschema.configuration as configuration
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.interfaces as _i
import ckanext.jsonschema.logic.get as _g
import ckanext.jsonschema.utils as utils

from jsonschema import Draft7Validator, RefResolver

log = logging.getLogger(__name__)

initialize_lock = threading.Lock()

def initialize():

    initialize_lock.acquire()

    if _c.JSON_CATALOG_INITIALIZED:
        initialize_lock.release()
        return

    log.info("Writing core schema files")

    try:
        initialize_core_schemas()
        reload()
        _c.JSON_CATALOG_INITIALIZED = True
    except Exception as e:
        _c.JSON_CATALOG_INITIALIZED = False
        
        log.error("Error initializing core schemas: " + str(e))
        raise e
    finally:
        initialize_lock.release()
    

def reload():
    
    _c.JSON_CATALOG.update({
        _c.JSON_SCHEMA_KEY: read_all_schema(),
        _c.JSON_TEMPLATE_KEY: read_all_template(),
        _c.JS_MODULE_KEY: read_all_module(),
        _c.JSON_REGISTRY_KEY: read_config()
    })

    jsonschema_plugins = _i.get_all_jsonschema_plugins()
            
    for plugin in jsonschema_plugins:
        try:
            plugin.register_jsonschema_resources()
        except TypeError:
            pass
    
def read_all_module():
    return utils._find_all_js(_c.PATH_MODULE)

def read_all_template():
    return utils._read_all_json(_c.PATH_TEMPLATE)

def read_all_schema():
    return utils._read_all_json(_c.PATH_SCHEMA)
    
def read_all_config():
    return utils._read_all_json(_c.PATH_CONFIG)

def read_config():
    return utils._json_load(_c.PATH_CONFIG, _c.FILENAME_REGISTRY)
    
def add_schemas_to_catalog(path):

    schemas = _c.JSON_CATALOG[_c.JSON_SCHEMA_KEY]
    schemas.update(utils._read_all_json(path))
    
def add_templates_to_catalog(path):

    schemas = _c.JSON_CATALOG[_c.JSON_TEMPLATE_KEY]
    schemas.update(utils._read_all_json(path))

def add_modules_to_catalog(path):

    schemas = _c.JSON_CATALOG[_c.JS_MODULE_KEY]
    schemas.update(utils._find_all_js(path))

def initialize_core_schemas():
    utils._initialize_license_schema()

def dataset_type(dataset):
    '''
    returns a jsonschema type based over dataset[type]
    '''
    if not dataset:
        raise Exception(_('The dataset is None!'))

    dataset_type = dataset.get('type')

    if not dataset_type:
        raise Exception(_('The resource has no format!'))
    
    #  # type has been properly configured only if it is matching the type-mapping
    # if dataset_type not in _c.TYPE_MAPPING.keys():
    #     raise Exception(_('Not recognized type: {}. Please check your configuration.').format(dataset_type))

    return dataset_type

def set_nested(dict, tuple, value):
    try:
        d = dict
        for k in tuple[:-1]:
            d = d.setdefault(k,{})
        d.update({tuple[-1:][0]:value})
    except:
        return None
    return dict

def pop_nested(dict, tuple):
    d = dict
    for k in tuple[:-1]:
        try:
            d = d[k]
        except:
            return
    try:
        d.pop(tuple[-1:][0])
    except:
        return # TODO errors?

def get_nested(dict, tuple):
    d = dict
    for k in tuple[:-1]:
        try:
            d = d[k]
        except:
            return
    try:
        return d[tuple[-1:][0]]
    except:
        return

def extend_nested(_dict, _tuple, _list):
    if not _dict or not _tuple or not _list:
        return
    try:
        d = _dict
        for k in _tuple[:-1]:
            d = d.setdefault(k,{})
        k = _tuple[-1:][0]
        if not d.get(k):
            d[k] = _list
        else:
            d[k].extend(_list)
    except:
        return
    return _dict

def map_to(from_dict, map, to_dict):
    errors=[]
    for (source_path, dest_path) in map.items():
        value = get_nested(from_dict, source_path)
        if value and not set_nested(to_dict, dest_path, value):
            errors.append({source_path, dest_path})
    return errors


def as_list_of_values(items, path, filter = lambda i : True, errors = None):
    if not items:
        return
    _items = []
    if not isinstance(items, list):
        items = [items]
    for _item in items:
        _i = get_nested(_item, path)
        if _i and filter(_i):
            _items.append(_i)
        # TODO error trap and return
    return _items

def as_list_of_dict(items, fields_map = None, filter = lambda i : True, errors = None):
    _items = []
    if not isinstance(items, list):
        items = [items]
    for _item in items:
        if _item and filter(_item):
            _i = {}
            
            if fields_map:
                errors = map_to(_item, fields_map, _i)
            else:
                _i = _item
            
            if _i: 
                _items.append(_i)
    return _items

def as_boolean(dict, path):
    '''
    if a value is found a conversion to boolean is provided
    return None
    '''
    # convert type
    b = get_nested(dict,path)
    if b and not isinstance(b, bool):
        if b.lower()=='true':
            set_nested(dict, path, True)
        else:
            set_nested(dict, path, False)

import datetime as dt


def as_datetime(dict, path, strptime_format='%Y-%m-%d'):
    #'%Y-%m-%d %H:%M:%S'
    d = get_nested(dict,path)
    if d and not isinstance(d, dt.date):
        try:
            return set_nested(dict, path, dt.datetime.strptime(d, strptime_format))
        except Exception as e:
            pass
        

# def map_inverse(to_dict, map, from_dict):
#     errors=[]
#     for (k,v) in inverted(map):
#         if not set_nested(to_dict, v, get_nested(from_dict, k)):
#             errors.append({k,v})
#     return errors

# https://github.com/jab/bidict/blob/0.18.x/bidict/__init__.py#L90
#from bidict import FrozenOrderedBidict, bidict, inverted 
# OVERWRITE
# OnDup, RAISE, DROP_OLD
# bidict, inverted, 
# class RelaxBidict(FrozenOrderedBidict):
    # __slots__ = ()
    # on_dup = OnDup(key=RAISE, val=DROP_OLD, kv=RAISE)
    # on_dup = OVERWRITE


def get_schema_of(_type):

    try:
        registry = configuration.get_registry()
        filename = registry.get(_type).get('schema')
    except:
        # the type could not be in the registry
        # it would be the case in nested references within schemas
        # in that case fetch the filename directly from the catalog
        filename = _type

    
    return _c.JSON_CATALOG[_c.JSON_SCHEMA_KEY].get(filename)
    
def get_template_of(_type):

    try:
        registry = configuration.get_registry()
        filename = registry.get(_type).get('template')
    except:
        filename = _type

    return _c.JSON_CATALOG[_c.JSON_TEMPLATE_KEY].get(filename, {})

def get_module_for(_type):

    try:
        registry = configuration.get_registry()
        filename = registry.get(_type).get('module')
    except:
        filename = _type

    return _c.JSON_CATALOG[_c.JS_MODULE_KEY].get(filename)

def get_body(dataset_id, resource_id = None):
    return get(dataset_id, resource_id, _c.SCHEMA_BODY_KEY)

def get_dataset_body(dataset):
    return _extract_from_dataset(dataset, _c.SCHEMA_BODY_KEY)

def get_resource_body(resource):
    return _extract_from_resource(resource, _c.SCHEMA_BODY_KEY)

def get_type(dataset_id, resource_id = None):
    return get(dataset_id, resource_id, _c.SCHEMA_TYPE_KEY)

# TODO check also validators.get_dataset_type
def get_dataset_type(dataset = None):
    return _get_dataset_type(dataset) or _extract_from_dataset(dataset, _c.SCHEMA_TYPE_KEY)

def get_resource_type(resource):
    return _extract_from_resource(resource, _c.SCHEMA_TYPE_KEY)

def get_opt(dataset_id, resource_id = None):
    return get(dataset_id, resource_id, _c.SCHEMA_OPT_KEY)

def get_dataset_opt(dataset):
    return _extract_from_dataset(dataset, _c.SCHEMA_OPT_KEY)

def get_resource_opt(resource):
    return _extract_from_resource(resource, _c.SCHEMA_OPT_KEY)

def get(dataset_id, resource_id = None, domain = None):
    
    try:
        pkg = dictize_pkg(_g.get_pkg(dataset_id))
    except toolkit.ObjectNotFound:
        raise toolkit.ObjectNotFound('Unable to find the requested dataset {}'.format(dataset_id))

    # we wanted the package
    if not resource_id and not domain:
        return pkg 

    if resource_id:
        for resource in pkg.get('resources'):
            _resource_id = resource.get('id')
            if _resource_id == resource_id:

                # we wanted the resource
                if not domain:
                    return resource
                
                # we wanted to extract something from the resource
                return _extract_from_resource(resource, domain)

        raise Exception('Unable to find the requested resource {}'.format(resource_id))

    # we wanted to extract something from the package
    return _extract_from_dataset(pkg, domain)

# def get_from_package(pkg, resource_id):
#     if not pkg:
#         raise Exception('Unable to find the requested dataset {}'.format(dataset_id))
#     if resource_id:
#         for resource in pkg.get('resources'):
#             _resource_id = resource.get('id')
#             if _resource_id == resource_id:
#                 return _extract_from_resource(resource)
#         raise Exception('Unable to find the requested resource {}'.format(resource_id))
#     return _extract_from_dataset(pkg)

####### Manipulate extraction context #######

def _extract_from_context(context, domain):

    if context and domain:
        return context.get(domain)
    
    raise Exception("Missing parameter resource or domain")

def get_context_body(context):
    return _extract_from_context(context, _c.SCHEMA_BODY_KEY)

def get_context_type(context):
    return _extract_from_context(context, _c.SCHEMA_TYPE_KEY)

def get_context_opt(context):
    return _extract_from_context(context, _c.SCHEMA_OPT_KEY)

def set_context_body(context, body):
    context[_c.SCHEMA_BODY_KEY] = body

def set_context_type(context, _type):
    context[_c.SCHEMA_TYPE_KEY] = _type

def set_context_opt(context, opt):
    context[_c.SCHEMA_OPT_KEY] = opt

def _extract_from_resource(resource, domain):

    # Checking extra data content for extration
    extras = resource.get('__extras')
    if not extras:
        # edit existing resource
        extras = resource

    if extras and domain:
        return extras.get(domain)
    
    raise Exception("Missing parameter resource or domain")

def _extract_from_dataset(dataset, domain):

    if dataset and domain:
        extras = dataset.get('extras')
        if extras and isinstance(extras, list):
            for e in extras:
                if e['key'] == domain:
                    return e['value']
    
    raise Exception("Missing parameter dataset or domain")


# TODO CKAN contribution
# TODO check also tools.get_dataset_type
def _get_dataset_type(data = None):
    
    _type = data and data.get('type')
    if _type:
        return _type

    from ckan.common import c

    # TODO: https://github.com/ckan/ckan/issues/6518
    path = c.environ['CKAN_CURRENT_URL']
    _type = path.split('/')[1]
    return _type

def update_extras_from_resource_context(resource, context):
    extras = resource.get('__extras')
    if not extras: 
        extras = {} #TODO this assumes the object comes from database
        resource['__extras'] = extras
    
    extras[_c.SCHEMA_BODY_KEY]=json.dumps(get_context_body(context))
    extras[_c.SCHEMA_TYPE_KEY]=get_context_type(context) # it is already a string
    extras[_c.SCHEMA_OPT_KEY]=json.dumps(get_context_opt(context))

# def update_extras_from_resource_context(data, extras):

#     # Checking extra data content for extration
#     for extra in data.get('__extras', []):
#         if key == _c.SCHEMA_BODY_KEY:
#             data['__extras'][key] = json.dumps(extras.get(_c.SCHEMA_BODY_KEY))
#         elif key == _c.SCHEMA_TYPE_KEY:
#             data['__extras'][key] = extras.get(_c.SCHEMA_TYPE_KEY)
#         elif key == _c.SCHEMA_VERSION_KEY:
#             data['__extras'][key] = extras.get(_c.SCHEMA_VERSION_KEY)
#         elif key == _c.SCHEMA_OPT_KEY:
#             data['__extras'][key] = json.dumps(extras.get(_c.SCHEMA_OPT_KEY))


def update_extras_from_context(data, extras):

    # Checking extra data content for extration
    for e in data.get('extras',[]):
        key = e.get('key')
        if not key:
            raise Exception('Unable to resolve extras with an empty key')
        if key == _c.SCHEMA_BODY_KEY:
            e['value'] = json.dumps(extras.get(_c.SCHEMA_BODY_KEY))
        elif key == _c.SCHEMA_TYPE_KEY:
            e['value'] = extras.get(_c.SCHEMA_TYPE_KEY)
        elif key == _c.SCHEMA_OPT_KEY:
            e['value'] = json.dumps(extras.get(_c.SCHEMA_OPT_KEY))


def update_extras(data, body, type, opt):
    # Checking extra data content for extration
    for e in data.get('extras',[]):
        key = e.get('key')
        if not key:
            raise Exception('Unable to resolve extras with an empty key')
        if key == _c.SCHEMA_BODY_KEY:
            e['value'] = json.dumps(body)
        elif key == _c.SCHEMA_TYPE_KEY:
            e['value'] = type
        elif key == _c.SCHEMA_OPT_KEY:
            e['value'] = json.dumps(opt)

def as_dict(field):

    value = encode_str(field)

    try:
        value = json.loads(value)
    except:
        pass

    return value

# REMOVE -> USE UTILS.
# TODO check utils
def as_json(value):

    value = encode_str(value)

    if isinstance(value, dict) or isinstance(value, list):
        try: 
            return json.dumps(value)
        except:
            pass
    elif isinstance(value, str):
        try: 
            return json.dumps(json.loads(value))
        except:
            pass
    return value


# def serializer(key, data, errors, context):

#     fd = data

#     for key in fd.keys():
#         value = fd[key]
#         if isinstance(fd[key], unicode):
#             value = value.encode('utf-8')

#         if isinstance(value, binary_type) or isinstance(value, str):
#             try: 
#                 fd[key] = json.loads(value)
#             except:
#                 fd[key] =  value

def render_template(template_name, extra_vars):

    import os

    import jinja2

    # setup for render
    templates_path = os.path.join(_c.PATH_ROOT, "jsonschema/templates")
    templateLoader = jinja2.FileSystemLoader(searchpath=templates_path)
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(template_name)
    
    # add helpers
    from ckan.plugins import get_plugin
    h = get_plugin(_c.TYPE).get_helpers()
    extra_vars['h'] = h

    try:
        return template.render(extra_vars)
    except jinja2.TemplateSyntaxError as e:
        log.error('Unable to interpolate line \'{}\'\nError:{}'.format(str(e.lineno), str(e)))
    except Exception as e:
        log.error('Exception: {}'.format(str(e)))



### FRAMEWORK MANIPULATIONS ###
# We would like to hide the extras from the package/resource when passing down to the plugins
# The following methods are used to remove the extras and then to put those back in

# def remove_jsonschema_extras_from_package_data(data):
#     '''
#     Clears data from jsonschema extras, so it seems like a clean CKAN package when passed into plugins
#     Returns the removed extras as a tuple (index, extra) so that they can be put back into data

#     '''

#     jsonschema_extras = []
#     filtered_extras = []

#     keys = [_c.SCHEMA_BODY_KEY, _c.SCHEMA_TYPE_KEY, _c.SCHEMA_OPT_KEY, _c.SCHEMA_VERSION_KEY]

#     for idx, extra in enumerate(data.get('extras')):
#         if extra.get('key') in keys:
#             jsonschema_extras.append((idx, extra))
#         else:
#             filtered_extras.append(extra)

#     data['extras'] = filtered_extras     
    
#     return jsonschema_extras

# def remove_jsonschema_extras_from_resource_data(data):
#     '''
#     Clears data from jsonschema extras, so it seems like a clean CKAN package when passed into plugins
#     Returns the removed extras as a tuple (index, extra) so that they can be put back into data
#     '''

#     jsonschema_extras = {}
#     filtered_extras = {}

#     keys = [_c.SCHEMA_BODY_KEY, _c.SCHEMA_TYPE_KEY, _c.SCHEMA_OPT_KEY, _c.SCHEMA_VERSION_KEY]

#     for key in data.get('__extras'):

#         value = data.get('__extras').get(key)

#         if key in keys:
#             jsonschema_extras[key] = value
#         else:
#             filtered_extras[key] = value

#     data['__extras'] = filtered_extras     
    
#     return jsonschema_extras

# def enrich_package_data_with_jsonschema_extras(data, extras):

#     for jsonschema_extra in extras:
#         position, element = jsonschema_extra
#         data['extras'].insert(position, element)
                

# def enrich_resource_data_with_jsonschema_extras(data, extras):

#     for key in extras:
#         value = extras[key]
#         data['__extras'][key] = value

###################################

def dictize_pkg(pkg):
    import ckan.lib.navl.dictization_functions as df
    fd = df.flatten_dict(pkg)
    for key in fd.keys():
        
        value = encode_str(fd[key])

        try: 
            fd[key] = json.loads(value)
        except:
            fd[key] =  value

    pkg = df.unflatten(fd)
    return pkg


def encode_str(value):

    from six import PY3, text_type

    if PY3 and isinstance(value, text_type):
        value = str(value)
    elif (not PY3) and isinstance(value, unicode):
        value = value.encode("utf-8")
    
    return value



class CustomRefResolver(RefResolver):

    def resolve(self, ref):
        '''
        Resolve the given reference.
        '''
        return ref, _c.JSON_CATALOG[_c.JSON_SCHEMA_KEY][ref]


_SCHEMA_RESOLVER = CustomRefResolver(
    base_uri='file://{}/'.format(_c.PATH_SCHEMA), 
    referrer=None
)

def draft_validation(schema, body, errors):
    """Validates ..."""

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

    return is_error



def format_number(n):
    import math
    
    millnames = ['',' Thousand',' Million',' Billion',' Trillion']

    n = float(n)
    millidx = max(0,min(len(millnames)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    return '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])
