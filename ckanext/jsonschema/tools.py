import ckan.lib.helpers as h
import ckan.plugins.toolkit as toolkit

_ = toolkit._
import json
import logging

import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.logic.get as _g
import ckanext.jsonschema.utils as utils
from ckanext.jsonschema.utils import encode_str

# import ckanext.jsonschema.logic.get as get

log = logging.getLogger(__name__)

def reload():

    # Initialize core generated schema
    try:
        initialize_core_schema()
        log.info("Initialized core schema")
    except Exception as e:
        log.error("Error initializing core schema: " + str(e))
        raise e


    # Append all the rest of the available schemas
    _c.JSON_CATALOG.update({
        _c.JSON_SCHEMA_KEY: read_all_schema(),
        _c.JSON_TEMPLATE_KEY: read_all_template(),
        _c.JS_MODULE_KEY: read_all_module()
    })
    

def read_all_module():
    return utils._find_all_js(_c.PATH_MODULE)

def read_all_template():
    return utils._read_all_json(_c.PATH_TEMPLATE)

def read_all_schema():
    return utils._read_all_json(_c.PATH_SCHEMA)

def initialize_core_schema():
    utils._initialize_core_schema()

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


def get_schema_of(type):
    return _c.JSON_CATALOG[_c.JSON_SCHEMA_KEY].get(type)

def get_template_of(type):
    return _c.JSON_CATALOG[_c.JSON_TEMPLATE_KEY].get(type)

def get_module_for(type):
    return _c.JSON_CATALOG[_c.JS_MODULE_KEY].get(type)

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
    return _extract_from_dataset(dataset, _c.SCHEMA_TYPE_KEY)\
        or _get_dataset_type(dataset)

def get_resource_type(resource):
    return _extract_from_resource(resource, _c.SCHEMA_TYPE_KEY)

def get_version(dataset_id, resource_id = None):
    return get(dataset_id, resource_id, _c.SCHEMA_VERSION_KEY)

def get_dataset_version(dataset):
    return _extract_from_dataset(dataset, _c.SCHEMA_VERSION_KEY)

def get_resource_version(resource):
    return _extract_from_resource(resource, _c.SCHEMA_VERSION_KEY)

def get_opt(dataset_id, resource_id = None):
    return get(dataset_id, resource_id, _c.SCHEMA_OPT_KEY)

def get_dataset_opt(dataset):
    return _extract_from_dataset(dataset, _c.SCHEMA_OPT_KEY)

def get_resource_opt(resource):
    return _extract_from_resource(resource, _c.SCHEMA_OPT_KEY)

def get(dataset_id, resource_id = None, domain = None):
    pkg = _g.get_pkg(dataset_id)
    if not pkg:
        raise Exception('Unable to find the requested dataset {}'.format(dataset_id))
    if resource_id:
        for resource in pkg.get('resources'):
            _resource_id = resource.get('id')
            if _resource_id == resource_id:
                return _extract_from_resource(resource, domain)
        raise Exception('Unable to find the requested resource {}'.format(resource_id))
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

def _extract_from_resource(resource, domain = None):
    if resource and domain:
        return resource.get(domain)
    else:
        return resource

def _extract_from_dataset(dataset, domain = None):

    if dataset and domain:
        extras = dataset.get('extras')
        if extras and isinstance(extras, list):
            for e in extras:
                if e['key'] == domain:
                    return e['value']
    else:
        return dataset

    

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

# def update_resource_extras(resource, extras):
#     resource[_c.SCHEMA_BODY_KEY]=json.dumps(extras.get(_c.SCHEMA_BODY_KEY))
#     resource[_c.SCHEMA_TYPE_KEY]=extras.get(_c.SCHEMA_TYPE_KEY)
#     resource[_c.SCHEMA_VERSION_KEY]=extras.get(_c.SCHEMA_VERSION_KEY)
#     resource[_c.SCHEMA_OPT_KEY]=json.dumps(extras.get(_c.SCHEMA_OPT_KEY))

def update_resource_extras(resource, body, type, opt, version):
    extras = resource.get('__extras')
    if not extras:
        extras = {}
        resource['__extras'] = extras
    
    extras[_c.SCHEMA_BODY_KEY]=json.dumps(body)
    extras[_c.SCHEMA_TYPE_KEY]=type
    extras[_c.SCHEMA_VERSION_KEY]=version
    extras[_c.SCHEMA_OPT_KEY]=json.dumps(opt)

def update_extras(data, extras):
    # Checking extra data content for extration
    for e in data.get('extras',[]):
        key = e.get('key')
        if not key:
            raise Exception('Unable to resolve extras with an empty key')
        if key == _c.SCHEMA_BODY_KEY:
            e['value'] = json.dumps(extras.get(_c.SCHEMA_BODY_KEY))
        elif key == _c.SCHEMA_TYPE_KEY:
            e['value'] = extras.get(_c.SCHEMA_TYPE_KEY)
        elif key == _c.SCHEMA_VERSION_KEY:
            e['value'] = extras.get(_c.SCHEMA_VERSION_KEY)
        elif key == _c.SCHEMA_OPT_KEY:
            e['value'] = json.dumps(extras.get(_c.SCHEMA_OPT_KEY))


def update_extras(data, body, type, opt, version):
    # Checking extra data content for extration
    for e in data.get('extras',[]):
        key = e.get('key')
        if not key:
            raise Exception('Unable to resolve extras with an empty key')
        if key == _c.SCHEMA_BODY_KEY:
            e['value'] = json.dumps(body)
        elif key == _c.SCHEMA_TYPE_KEY:
            e['value'] = type
        elif key == _c.SCHEMA_VERSION_KEY:
            e['value'] = version
        elif key == _c.SCHEMA_OPT_KEY:
            e['value'] = json.dumps(opt)

def as_dict(field):

    value = encode_str(field)

    try:
        value = json.loads(value)
    except:
        pass

    return value


# TODO check utils
def as_json(field):
    value = field

    if isinstance(field, unicode):
        value = value.encode('utf-8')
    if isinstance(value, dict):
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

def resolve_resource_extras(dataset_type, resource, _as_dict = False):
    from ckanext.jsonschema.plugin import handled_resource_types
    # Pre-setting defaults
    resource_types = handled_resource_types(dataset_type)
    if resource_types:
        _type = resource_types[0]
        body = get_template_of(_type)
    else:
        _type = None
        body = {}
    
    opt = dict(_c.SCHEMA_OPT)
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
    
    if _as_dict:
        body = as_dict(body)
        opt = as_dict(opt)
    else:
        body = as_json(body)
        opt = as_json(opt)
    
    return {
        _c.SCHEMA_OPT_KEY : opt,
        _c.SCHEMA_BODY_KEY: body,
        _c.SCHEMA_TYPE_KEY: _type,
        _c.SCHEMA_VERSION_KEY: version
    }

def resolve_extras(data, _as_dict = False):
    # Pre-setting defaults
    _type = get_dataset_type(data)
    body = get_template_of(_type)
    opt = dict(_c.SCHEMA_OPT)
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
    
    if _as_dict:
        body = as_dict(body)
        opt = as_dict(opt)
    else:
        body = as_json(body)
        opt = as_json(opt)
    
    return {
        _c.SCHEMA_OPT_KEY : opt,
        _c.SCHEMA_BODY_KEY: body,
        _c.SCHEMA_TYPE_KEY: _type,
        _c.SCHEMA_VERSION_KEY: version
    }




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

