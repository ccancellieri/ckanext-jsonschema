import ckan.lib.helpers as h
import ckan.plugins.toolkit as toolkit
_ = toolkit._
from requests.models import InvalidURL
import json

# import ckanext.jsonschema.logic.get as get
# import ckanext.jsonschema.validators as v
import logging
log = logging.getLogger(__name__)

import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.utils as utils

def read_all_module():
    return utils._find_all_js(_c.PATH_MODULE)

def read_all_template():
    return utils._read_all_json(_c.PATH_TEMPLATE)

def read_all_schema():
    return utils._read_all_json(_c.PATH_SCHEMA)

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

import six
import jinja2
Environment = jinja2.environment.Environment
FunctionLoader = jinja2.loaders.FunctionLoader 
TemplateSyntaxError = jinja2.TemplateSyntaxError

# from jinja2.utils import select_autoescape
def interpolate_fields(model, template):
    ###########################################################################
    # Jinja2 template
    ###########################################################################
    
    def functionLoader(name):
        return template[name]

    env = Environment(
                loader=FunctionLoader(functionLoader),
                # autoescape=select_autoescape(['html', 'xml']),
                autoescape=True,
                #newline_sequence='\r\n',
                trim_blocks=False,
                keep_trailing_newline=True)

    for f in template.keys():
        if isinstance(template[f],six.string_types):
            try:
                _template = env.get_template(f)
                template[f] = _template.render(model)
            except TemplateSyntaxError as e:
                raise Exception(_('Unable to interpolate field \'{}\' line \'{}\''.format(f,str(e.lineno))))
            except Exception as e:
                raise Exception(_('Unable to interpolate field \'{}\': {}'.format(f,str(e))))

    return template
    ###########################################################################