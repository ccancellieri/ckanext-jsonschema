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
    
     # type has been properly configured only if it is matching the type-mapping
    if dataset_type not in _c.TYPE_MAPPING.keys():
        raise Exception(_('Not recognized type: {}. Please check your configuration.').format(dataset_type))

    return dataset_type

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