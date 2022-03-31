import ckan.plugins.toolkit as toolkit
from ckan.logic import ValidationError

_ = toolkit._
import json
import logging
import os

import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.interfaces as _i
import ckanext.jsonschema.logic.get as _g
import ckanext.jsonschema.tools as _t

from ckan.plugins.toolkit import get_or_bust, h

log = logging.getLogger(__name__)

def get_view_body(view):
    return _extract_from_view(view, _c.SCHEMA_BODY_KEY)

def get_view_type(view):
    return _extract_from_view(view, _c.SCHEMA_TYPE_KEY)

def get_view_opt(view):
    return _extract_from_view(view, _c.SCHEMA_OPT_KEY)

def _extract_from_view(view, domain):
    
    if view and domain:
        return view.get(domain)
    
    raise Exception("Missing parameter resource or domain")

def interpolate_fields(model, template, view_type):

    def functionLoader(_template):
        return _template

    import jinja2
    Environment = jinja2.environment.Environment
    FunctionLoader = jinja2.loaders.FunctionLoader 
    TemplateSyntaxError = jinja2.TemplateSyntaxError

    env = Environment(
        loader=FunctionLoader(functionLoader),
        autoescape=False,
        trim_blocks=False,
        keep_trailing_newline=True
    )

    _enhance_model_with_data_helpers(model, template, view_type)
    
    try:
        polished_template = json.dumps(template).replace('"{{',"{{").replace('}}"', '}}')
        _template = env.get_template(polished_template)
        template = json.loads(_template.render(model))

    except TemplateSyntaxError as e:
        message = _('Unable to interpolate field on line \'{}\'\nError:{}'.format(str(e.lineno),str(e)))
        raise ValidationError({'message': message}, error_summary = message)
    except Exception as e:
        message = _('Unable to interpolate field: {}'.format(str(e)))
        raise ValidationError({'message': message}, error_summary = message)

    #return dictize_pkg(template)
    return template

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

def get_interpolated_view_model(view_body, view_type):

    view_body = get_view_body(view)
    if not view_body:
        raise Exception(_('Unable to find a valid configuration for view ID: {}'.format(str(view.get('id')))))

    view_type = view.get("view_type") 

    model = _get_model(package_id=get_or_bust(view,'package_id'), resource_id=get_or_bust(view,'resource_id'))
    
    return interpolate_fields(model, view_body, view_type)

def _get_model(package_id, resource_id):
    '''
    Returns the model used by jinja2 template
    '''

    if not package_id or not resource_id:
        raise Exception('wrong parameters we expect a package_id and a resource_id')

    # TODO can we have a context instead of None?
    pkg = toolkit.get_action('package_show')(None, {'id':package_id})
    if not pkg:
        raise Exception('Unable to find package, check input params')

    pkg = _t.dictize_pkg(pkg)

    # res = filter(lambda r: r['id'] == view.resource_id,pkg['resources'])[0]
    res = next(r for r in pkg['resources'] if r['id'] == resource_id)
    if not res:
        raise Exception('Unable to find resource under this package, check input params')

    organization_id = pkg.get('owner_org')

    # return the model as dict
    _dict = {
        'package': pkg,
        'organization': toolkit.get_action('organization_show')(None, {'id': organization_id}),
        'resource':res,
        'ckan':{'base_url':h.url_for('/', _external=True)},
        #'data': {} #TODO
        }

    return _dict 

def _enhance_model_with_data_helpers(model, template, view_type):
    '''
    This methods adds data helpers from plugins to the model provided to the template renderer
    Plugins implementing the IJsonschemaView interface can define the method get_data_helpers which returns a list of function
    The function are injected with their name in the environment of jinja
    '''

    resource = model['resource']
    
    plugin = next(plugin for plugin in _i.JSONSCHEMA_IVIEW_PLUGINS if plugin.info().get('name') == view_type)
    data_helpers = plugin.get_data_helpers(view_type, template, resource)

    # TODO CHECK FOR CONFLICTS
    model.update(data_helpers)

def get_resource_content(resource):
    '''
    Plugin that implement IJsonschemaView should call this to get the resource content depending on the type of the resource
    '''

    # TODO understand resource type jsonschema, url, localfile
    # TODO query resource options for customized logic on where to pick up data
    
    is_jsonschema = _t.get_resource_type(resource) != None
    is_upload = resource.get('url_type') == 'upload'
    is_url = resource.get('url') and resource.get('url_type') == None

    resource_content = {}
    if is_jsonschema:
        resource_content = load_resource_content_from_jsonschema_body(resource)
    elif is_upload:
        resource_content = load_resource_content_from_disk(resource)
    elif is_url:
        resource_content = load_resource_content_from_url(resource)

    return resource_content

def load_resource_content_from_jsonschema_body(resource):
    return _t.get_resource_body(resource)

def load_resource_content_from_disk(resource):
    import json

    import ckan.lib.uploader as uploader

    upload = uploader.get_resource_uploader(resource)
    filepath = upload.get_path(resource['id'])

    with open(filepath) as f:
        resource_content = json.loads(f.read())
    
    return resource_content

def load_resource_content_from_url(resource):
    import requests

    url = resource.get('url') 
    resource_content = requests.get(url).json()

    return resource_content

def wrap_view(view, content):

    view_type = view.get("view_type") 

    plugin = next(plugin for plugin in _i.JSONSCHEMA_IVIEW_PLUGINS if plugin.info().get('name') == view_type)
    content = plugin.wrap_view(view_type, content)
    return content

#### VIEW CONFIGURATION #####

VIEWS_KEY = 'views'
OPT_KEY = 'opt'
INFO_KEY = 'info'

def get_views(config):
    return config.get(VIEWS_KEY)

def get_opt(config):
    return config.get(OPT_KEY, {})

def get_info(config):
    return config.get(INFO_KEY)

def get_view_jsonshema_types(config, resource):
    # Takes also the resource
    # Could filter view types based on format or resource jsonschema type

    view_types = []

    views = get_views(config)
    for view in views:
        view_jsonschema_types_list = view.get(_c.VIEW_JSONSCHEMA_TYPE)
        for view_jsonschema_type in view_jsonschema_types_list: 
            if view_jsonschema_type not in view_types:
                view_types.append(view_jsonschema_type)

    return view_types

def is_jsonschema_view(view_type):

    for plugin in _i.JSONSCHEMA_IVIEW_PLUGINS:
        info = plugin.info()

        if info['name'] == view_type:
            return True

    return False
        
def get_view_configuration(config, resource_format, resource_jsonschema_type=None):
    '''
    Returns the first (could be more than one) view configuration that matches the given resource 
    '''
    
    for view in get_views(config):

        format_matches = view.get(_c.RESOURCE_FORMAT) == resource_format or view.get(_c.WILDCARD_FORMAT, False) == True
            
        if format_matches:
            
            match_only_format = not resource_jsonschema_type and not (_c.RESOURCE_JSONSCHEMA_TYPE in view)


            if match_only_format:
                return view


            else:
                available_for_all_resource_jsonschema_types = view.get(_c.WILDCARD_JSONSCHEMA_TYPE, False) == True
                jsonschema_type_matches = (resource_jsonschema_type and resource_jsonschema_type in view.get(_c.RESOURCE_JSONSCHEMA_TYPE, [])) 
                
                if available_for_all_resource_jsonschema_types or jsonschema_type_matches:
                    return view
        
    return None

# def get_schema(config, format, jsonschema_type=None):
    
#     catalog_key = get_schema_type(config, format, jsonschema_type)
#     schema = _c.JSON_CATALOG[_c.JSON_SCHEMA_KEY].get(catalog_key) 
#     return schema

# def get_schema_type(config, format, jsonschema_type=None):
#     view = _get_view(config, format, jsonschema_type)
#     return _u._get_key(view.get('schema'))

# def get_template(config, format, jsonschema_type=None):
#     view = _get_view(config, format, jsonschema_type)

#     view_template = view.get('template')
#     template = {}
    
#     if view_template:
#         catalog_key = _u._get_key(view.get('template'))
#         template = _c.JSON_CATALOG[_c.JSON_TEMPLATE_KEY].get(catalog_key) 
        
#     return template

def get_all_schemas_in_config(config):

    config_views = config.get(VIEWS_KEY)
    schemas = [view['schema'] for view in config_views if 'schema' in view]
    
    return schemas

def get_all_templates_in_config(config):

    config_views = config.get(VIEWS_KEY)
    schemas = [view['template'] for view in config_views if 'template' in view]
    
    return schemas

def get_all_modules_in_config(config):

    config_views = config.get(VIEWS_KEY)
    schemas = [view['module'] for view in config_views if 'module' in view]
    
    return schemas


def _copy_to_jsonschema(source_base, destination, files):
    '''
    This method copies files from source_base to Jsonschema's destination folder
    The files parameter is the list of files to copy
    For each file, it retrieves <source_base>/<file> and copies it into <jsonschema>/<destinatiion>

    Example: add_files_to_jsonschema(source_base, 'schema', [])
    '''

    for file in files:
               
        complete_absolute_plugin_path = os.path.join(source_base, file)
        complete_absolute_jsonschema_path = os.path.join(destination, file)

        if not os.path.exists(os.path.dirname(complete_absolute_jsonschema_path)):
            os.makedirs(os.path.dirname(complete_absolute_jsonschema_path))
        
        # check if overwrites
        os.popen('cp {} {}'.format(complete_absolute_plugin_path, complete_absolute_jsonschema_path)) 