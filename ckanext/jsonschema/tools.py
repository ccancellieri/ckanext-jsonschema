import threading

import ckan.plugins.toolkit as toolkit

_ = toolkit._
import json
import logging
import os

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

    log.info("Initialize core schema files")

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
        _c.JSON_REGISTRY_KEY: read_registry()
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

def read_registry():
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

########################  REGISTRY ############################## 

def get_from_registry(_type):
    registry = configuration.get_registry()
    return registry.get(_type)

def add_to_registry(path, filename_registry):
    registry = configuration.get_registry()
    plugin_registry = utils._json_load(path, filename_registry)
    registry.update(plugin_registry)


def get_label_from_registry(_type):
    registry_entry = get_from_registry(_type)

    if registry_entry:
        return registry_entry.get('label', _type)
    else:
        return _type

def is_supported_ckan_field(jsonschema_type, field):

    registry_entry = get_from_registry(jsonschema_type)

    # If not in registry, we want default behaviour (render CKAN's fields)
    if not registry_entry:
        return True

    if registry_entry.get(_c.WILDCARD_CKAN_FIELDS, False):
        return True

    supported_ckan_fields = registry_entry.get(_c.SUPPORTED_CKAN_FIELDS, [])
    return field in supported_ckan_fields


def is_supported_jsonschema_field(jsonschema_type, field):

    registry_entry = get_from_registry(jsonschema_type)
    
    # If not in registry, we want default behaviour (don't render jsonschema)
    if not registry_entry:
        return False

    if registry_entry.get(_c.WILDCARD_JSONSCHEMA_FIELDS, False):
        return True

    supported_jsonschema_fields = registry_entry.get(_c.SUPPORTED_JSONSCHEMA_FIELDS, [])
    return field in supported_jsonschema_fields


def get_schema_of(_type):
    return _find_in_registry_or_catalog(_type, _c.JSON_SCHEMA_KEY)

def get_template_of(_type):
    return _find_in_registry_or_catalog(_type, _c.JSON_TEMPLATE_KEY)

def get_module_for(_type):
    return _find_in_registry_or_catalog(_type, _c.JS_MODULE_KEY)


def _find_in_registry_or_catalog(item, sub):
    try:
        registry = configuration.get_registry()
        filename = registry.get(item).get(sub)
    except:
        # the type could not be in the registry
        # it would be the case in nested references within schemas
        # in that case fetch the filename directly from the catalog
        filename = item

    return _c.JSON_CATALOG[sub].get(filename)

###################################################### 

def get_body(dataset_id, resource_id = None):
    return get(dataset_id, resource_id, _c.SCHEMA_BODY_KEY)

def safe_helper(helper, data, default_return = {}):
    try:
        return helper(data)
    except:
        return default_return

def get_package_body(package):
    return _extract_from_package(package, _c.SCHEMA_BODY_KEY)

def get_resource_body(resource):
    return _extract_from_resource(resource, _c.SCHEMA_BODY_KEY)

def set_resource_body(resource, value):
    _set_into_resource(resource, _c.SCHEMA_BODY_KEY, value)

def get_type(dataset_id, resource_id = None):
    return get(dataset_id, resource_id, _c.SCHEMA_TYPE_KEY)

# TODO check also validators.get_package_type
def get_package_type(package = None):
    return _get_package_type(package) or _extract_from_package(package, _c.SCHEMA_TYPE_KEY)

def get_resource_type(resource):
    return _extract_from_resource(resource, _c.SCHEMA_TYPE_KEY, default_value = None)

def set_resource_type(resource, value):
    _set_into_resource(resource, _c.SCHEMA_TYPE_KEY, value)

def get_opt(dataset_id, resource_id = None):
    return get(dataset_id, resource_id, _c.SCHEMA_OPT_KEY)

def get_package_opt(package):
    return _extract_from_package(package, _c.SCHEMA_OPT_KEY)

def get_resource_opt(resource):
    return _extract_from_resource(resource, _c.SCHEMA_OPT_KEY)

def set_resource_opt(resource, value):
    _set_into_resource(resource, _c.SCHEMA_OPT_KEY, value)

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
    return _extract_from_package(pkg, domain)


def _extract_from_resource(resource, domain, default_value = {}):

    # Checking extra data content for extration
    extras = resource.get('__extras')
    if not extras:
        # edit existing resource
        extras = resource

    if extras and domain:
        # TODO: May fail fast
        return extras.get(domain, default_value)
    
    raise Exception("Missing parameter resource or domain")

def _set_into_resource(resource, domain, value):
    
    # Checking extra data content for extration
    extras = resource.get('__extras')
    if not extras:
        # edit existing resource
        extras = resource

    if extras and domain:
        # TODO: May fail fast
        extras[domain] = value
        return resource
    
    raise Exception("Missing parameter resource or domain")


def _extract_from_package(dataset, domain, default_value = {}):

    if dataset and domain:
        return dataset.get(domain, default_value)
        
    raise Exception("Missing parameter dataset or domain")
    
    
# TODO CKAN contribution
# TODO check also tools.get_package_type
def _get_package_type(data = None):
    
    
    _type = data and data.get('type')

    # TODO
    # if not _type and toolkit.c.pkg_dict:
    #   _type = toolkit.c.pkg_dict.get('type')

    if _type:
        return _type

    from ckan.common import c

    # TODO: https://github.com/ckan/ckan/issues/6518
    path = c.environ['CKAN_CURRENT_URL']
    _type = path.split('/')[1]
    return _type


# def update_extras(data, body, type, opt):
#     # Checking extra data content for extration
#     for e in data.get('extras',[]):
#         key = e.get('key')
#         if not key:
#             raise Exception('Unable to resolve extras with an empty key')
#         if key == _c.SCHEMA_BODY_KEY:
#             e['value'] = json.dumps(body)
#         elif key == _c.SCHEMA_TYPE_KEY:
#             e['value'] = type
#         elif key == _c.SCHEMA_OPT_KEY:
#             e['value'] = json.dumps(opt)

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

# def render_template(template_name, extra_vars):

#     import os

#     import jinja2

#     # setup for render
#     templates_paths = [
#         os.path.join(_c.PATH_ROOT, "jsonschema/templates"),
#         os.path.join(_c.PATH_ROOT, "jsonschema/iso19139/templates"), #TODO should get from plugins
#     ]
#     templateLoader = jinja2.FileSystemLoader(searchpath=templates_paths)
#     templateEnv = jinja2.Environment(loader=templateLoader)
#     template = templateEnv.get_template(template_name)
    
#     # add helpers
#     from ckan.plugins import get_plugin
#     h = get_plugin(_c.TYPE).get_helpers()
#     extra_vars['h'] = h

#     try:
#         return template.render(extra_vars)
#     except jinja2.TemplateSyntaxError as e:
#         log.error('Unable to interpolate line \'{}\'\nError:{}'.format(str(e.lineno), str(e)))
#     except Exception as e:
#         log.error('Exception: {}'.format(str(e)))


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

    # def resolve_fragment(self, doc, frag):
    #     return super(RefResolver, self).resolve_fragment(doc, frag)

    def resolve_from_url(self, url):
        """
        Resolve the given remote URL.
        """

        import os
        import jsonschema.exceptions as exceptions
        from jsonschema.compat import urldefrag

        url, fragment = urldefrag(url)
        try:
            # path = os.path.join(_c.PATH_SCHEMA, url)
            # self.base_uri
            # self.pop_scope()
            scope = None
            if self.resolution_scope.lower().endswith('.json'):                
                scope = self.resolution_scope
                self.pop_scope()
                resolved = self.resolve_from_url(url)
                self.push_scope(scope)
                return resolved

            full_uri = os.path.relpath(os.path.join(self.resolution_scope, url))
            
            # full_uri = os.path.relpath(os.path.join(self.base_uri, url))
            document = _c.JSON_CATALOG[_c.JSON_SCHEMA_KEY][full_uri]
        except KeyError:
            try:
                document = self.resolve_remote(url)
            except Exception as exc:
                raise exceptions.RefResolutionError(exc)

        return self.resolve_fragment(document, fragment)


def draft_validation(jsonschema_type, body, errors):
    """Validates ..."""

    registry_entry = get_from_registry(jsonschema_type)

    filename = registry_entry['schema']

    schema = get_schema_of(jsonschema_type)

    return _draft_validation(filename, schema, body, errors)


def _draft_validation(jsonschema_file, schema, body, errors):
    """Validates ..."""

    BASE_URI = os.path.dirname(jsonschema_file)
        
    _SCHEMA_RESOLVER = CustomRefResolver(
        base_uri=BASE_URI,
        referrer=None,
        # store=_c.JSON_CATALOG[_c.JSON_SCHEMA_KEY]
    )

    validator = Draft7Validator(schema, resolver=_SCHEMA_RESOLVER)

    # For each error, build the error message for the frontend with the path and the message
    is_error = False

    for idx, error in enumerate(sorted(validator.iter_errors(body), key=str)):
        
        is_error = True

        error_path = 'Root'

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


def url_quote(url):
    import urllib
    return urllib.quote(url)