import threading

import ckan.plugins.toolkit as toolkit

_ = toolkit._
import json
import logging

import ckanext.jsonschema.configuration as configuration
import ckanext.jsonschema.view_configuration as view_configuration
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.logic.get as _g
import ckanext.jsonschema.utils as utils


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
        _c.JSON_CONFIG_KEY: read_all_config(),
        _c.JSON_VIEW_CONFIG_KEY: read_all_view_config()
    })

    configuration.setup()
    view_configuration.setup()
    
    
def read_all_module():
    return utils._find_all_js(_c.PATH_MODULE)

def read_all_template():
    return utils._read_all_json(_c.PATH_TEMPLATE)

def read_all_schema():
    return utils._read_all_json(_c.PATH_SCHEMA)
    
def read_all_config():
    return utils._read_all_json(_c.PATH_CONFIG)
    
def read_all_view_config():
    return utils._read_all_json(_c.PATH_VIEW_CONFIG)

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
    return _get_dataset_type(dataset) or _extract_from_dataset(dataset, _c.SCHEMA_TYPE_KEY)

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

def get_context_version(context):
    return _extract_from_context(context, _c.SCHEMA_VERSION_KEY)

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
    extras[_c.SCHEMA_VERSION_KEY]=json.dumps(get_context_version(context))
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

# REMOVE -> USE UTILS.
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

# def resolve_resource_extras(dataset_type, resource, _as_dict = False):
#     from ckanext.jsonschema.plugin import handled_resource_types
#     # Pre-setting defaults
#     resource_types = handled_resource_types(dataset_type)
#     if resource_types:
#         _type = resource_types[0]
#         body = get_template_of(_type)
#     else:
#         _type = None
#         body = {}
    
#     opt = dict(_c.SCHEMA_OPT)
#     version = _c.SCHEMA_VERSION

#     # Checking extra data content for extration
#     e = resource.get('__extras',{})
#     if not e:
#         # edit existing resource
#         e = resource

#     body = e.get(_c.SCHEMA_BODY_KEY, body)
#     _type = e.get(_c.SCHEMA_TYPE_KEY, _type)
#     version = e.get(_c.SCHEMA_VERSION_KEY, version)
#     opt = e.get(_c.SCHEMA_OPT_KEY, opt)
    
#     if _as_dict:
#         body = as_dict(body)
#         opt = as_dict(opt)
#     else:
#         # REMOVE AS_JSON
#         body = as_json(body)
#         opt = as_json(opt)
    
#     return {
#         _c.SCHEMA_OPT_KEY : opt,
#         _c.SCHEMA_BODY_KEY: body,
#         _c.SCHEMA_TYPE_KEY: _type,
#         _c.SCHEMA_VERSION_KEY: version
#     }

# def resolve_extras(data, _as_dict = False):
#     # Pre-setting defaults
#     _type = get_dataset_type(data)
#     body = get_template_of(_type)
#     opt = dict(_c.SCHEMA_OPT)
#     version = _c.SCHEMA_VERSION

#     # Checking extra data content for extration
#     for e in data.get('extras',[]):
#         key = e.get('key')
#         if not key:
#             raise Exception('Unable to resolve extras with an empty key')
#         if key == _c.SCHEMA_BODY_KEY:
#             body = e['value']
#         elif key == _c.SCHEMA_TYPE_KEY:
#             _type = e['value']
#         elif key == _c.SCHEMA_VERSION_KEY:
#             version = e['value']
#         elif key == _c.SCHEMA_OPT_KEY:
#             opt = e['value']
    
#     if _as_dict:
#         body = as_dict(body)
#         opt = as_dict(opt)
#     else:
#         body = as_json(body)
#         opt = as_json(opt)
    
#     return {
#         _c.SCHEMA_OPT_KEY : opt,
#         _c.SCHEMA_BODY_KEY: body,
#         _c.SCHEMA_TYPE_KEY: _type,
#         _c.SCHEMA_VERSION_KEY: version
#     }




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


################################ VIEWS ########################################
def get_config(view_id):

    view = view_id and query.view_by_id(view_id)
    if not view:
        raise Exception(_('No view found for view_id: {}'.format(str(view_id))))

    view_config = view.get('config',None)
    if not view_config:
        raise Exception(_('Unable to find a valid configuration for view ID: {}'.format(str(view_id))))

    type = view_config and view_config.get(constants.TERRIAJS_TYPE_KEY,None)
    if not type:
        raise Exception(_('No type found for view: {}'.format(str(view_id))))

    model = _get_model(dataset_id=toolkit.get_or_bust(view,'package_id'),resource_id=toolkit.get_or_bust(view,'resource_id'))
    terriajs_config = toolkit.get_or_bust(view_config,constants.TERRIAJS_CONFIG_KEY)
    
    # backward compatibility (the string is now stored as dict)
    if not isinstance(terriajs_config,dict):
        terriajs_config = json.loads(terriajs_config)

    # Interpolation
    _terriajs_config = interpolate_fields(model,terriajs_config)

    camera={
        'east':view_config.get('east',180),
        'west':view_config.get('west',-180),
        'north':view_config.get('north',90),
        'south':view_config.get('south',-90)
    }
    return { 'config':_terriajs_config, 'type':type, 'camera':camera }


def get_model(package_id, resource_id):
    '''
    Returns the model used by jinja2 template
    '''

    if not package_id or not resource_id:
        raise Exception('wrong parameters we expect a package_id and a resource_id')

    # TODO can we have a context instead of None?
    pkg = toolkit.get_action('package_show')(None, {'id': package_id})
    if not pkg:
        raise Exception('Unable to find dataset, check input params')

    pkg = dictize_pkg(pkg)

    # res = filter(lambda r: r['id'] == view.resource_id,pkg['resources'])[0]
    res = next(r for r in pkg['resources'] if r['id'] == resource_id)

    plugin = view_configuration.get_plugin(res.get_or_bust('format', get_resource_type(res)))
    data = plugin.interpolate_data(res)

    if not res:
        raise Exception('Unable to find resource under this dataset, check input params')

    # return the model as dict
    _dict = {
        'dataset':pkg,
        'organization': toolkit.get_or_bust(pkg,'organization'),
        'resource':res,
        'data': data,
        'ckan':{'base_url':toolkit.h.url_for('/', _external=True)},
        'terriajs':{'base_url': constants.TERRIAJS_URL}
        }

    return _dict 

def interpolate_fields(model, template):
    # What kind of object is template?


    ###########################################################################
    # Jinja2 template
    ###########################################################################


    for f in template.keys():
        if f in constants.FIELDS_TO_SKIP:
            continue
        

        interpolate = False

        if PY3:
            # TODO check python3 compatibility 'unicode' may disappear?
            if isinstance(template[f],(str)):
                interpolate = True
        elif isinstance(template[f],(str,unicode)):
                interpolate = True
        
    
        if interpolate:
            template = render_template(model, template)

    return template
    ###########################################################################
