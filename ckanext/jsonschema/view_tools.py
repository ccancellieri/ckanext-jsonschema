import ckan.plugins.toolkit as toolkit
from ckan.logic import ValidationError

_ = toolkit._
import json
import logging
import os

import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.interfaces as _i
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.logic.get as _g

from ckan.plugins.toolkit import h

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

def interpolate_fields(model, template):

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
    
    try:
        
        # We can have
        # "{{array}}"  : {{array}}

        # big_query_value
        # "{{number}}" : {{number}}

        # "text {{number}}" : "text {{number}}"
        #  "{{number}} text" : "{{number}} text"
        # "{{string}}" : "{{string}}"
        # "a {{number}} b" : "a {{number}} b"
        # "a {{string}} b" : "a {{string}} b"
        
        # "{{metodo()}}" -> {{metodo}}
        # "{{resource.id}}" -> "{{resource.id}}"

        # "{{.*()}}" -> {{}}
        
        import re

        method_recognize_regex = '\"(\{\{[a-zA-Z0-9\.\_\-]+\([a-zA-Z0-9\, \.\_\-]*\)\}\})\"'
        output_regex = '\g<1>'
        _template = None
        rendered = ''
        
        ## TEMPLATE SETUP
        
        # json.dumps double escapes strings (if there was a \n in template, becomes \\n) and this breaks jinja
        # with the decode the double escape is reverted
        polished_template = json.dumps(template).decode("unicode-escape")

        # apply the regex to find custom jinja functions and remove quotes
        polished_template = re.sub(method_recognize_regex, output_regex, polished_template)
        
        _template = env.get_template(polished_template)
        
        rendered = _template.render(model)

        # We use strict false so that control characters such as \n don't break json.loads
        template = json.loads(rendered, strict=False)

    except TemplateSyntaxError as e:
        message = 'Unable to interpolate field on line \'{}\' Error:\'{}\' Value:\'{}\''\
            .format(str(e.lineno),str(e.message), e.source)
        raise ValidationError({'message': message}, error_summary = message)
    except Exception as e:
        message = 'Exception: \'{}\' Rendered: \'{}\''.format(str(e), rendered)
        raise ValidationError({'message': message}, error_summary = message)

    #return dictize_pkg(template)
    return template

def get_model(package_id, resource_id):
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


    # In interpolate_fields, when jinja tries to render the model, if the model contains invalid characters (eg degrees symbol) 
    # it crashes due to encoding issues:
    #       'ascii' codec can't decode byte 0xc2 in position 599: ordinal not in range(128)' 
    # So we re-encode the model for special characters
    model = json.loads(json.dumps(_dict).encode('utf-8'))

    return model 

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
    # view_types = []

    # views = get_views(config)
    # for view in views:
    #     view_jsonschema_types_list = view.get(_c.VIEW_JSONSCHEMA_TYPE)
    #     for view_jsonschema_type in view_jsonschema_types_list: 
    #         if view_jsonschema_type not in view_types:
    #             view_types.append(view_jsonschema_type)

    # return view_types

    resource_format = resource.get('format')
    resource_jsonschema_type = _t.get_resource_type(resource)
    view_configuration = get_view_configuration(config, resource_format, resource_jsonschema_type)
    return view_configuration.get(_c.VIEW_JSONSCHEMA_TYPE)

def is_jsonschema_view(view_type):
    return get_jsonschema_view_plugin(view_type) != None
        

def get_jsonschema_view_plugin(view_type):

    for plugin in _i.JSONSCHEMA_IVIEW_PLUGINS:
        info = plugin.info()

        if info['name'] == view_type:
            return plugin

    return None

def rendered_resource_view(resource_view, resource, package):
    '''
    Returns a rendered resource view snippet.
    '''
    view_type = resource_view['view_type']

    # the two plugins may match
    # import ckan.lib.datapreview as datapreview
    # view_plugin = datapreview.get_view_plugin(view_type)
    view_plugin = get_jsonschema_view_plugin(view_type)
    
    if not view_plugin:
        return 'No plugin found for view_type: {}'.format(view_type)
    
    context = {}
    data_dict = {'resource_view': resource_view,
                 'resource': resource,
                 'package': package}
    vars = view_plugin.setup_template_variables(context, data_dict) or {}
    template = view_plugin.view_template(context, data_dict)
    data_dict.update(vars)
    from webhelpers.html import literal
    import ckan.lib.base as base
    return literal(base.render(template, extra_vars=data_dict))


def get_view_configuration(config, resource_format, resource_jsonschema_type=None):
    '''
    Returns the first (could be more than one) view configuration that matches the given resource 
    '''
    
    if not resource_format:
        return None

    resource_format = resource_format.lower()

    for view in get_views(config):

        format_matches = resource_format in view.get(_c.RESOURCE_FORMATS, []) or view.get(_c.WILDCARD_FORMAT, False) == True
            
        if format_matches:
            
            match_only_format = not resource_jsonschema_type and not (_c.RESOURCE_JSONSCHEMA_TYPE in view)


            if match_only_format:
                return view


            else:
                # The wildcard allows also for views without jsonschema_type(s)
                # Maybe add a specific option in the configuration? (available_for_resources_without_)
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



def get_view_types():

    view_types = []

    for plugin in _i.JSONSCHEMA_IVIEW_PLUGINS:
        name = plugin.info().get('name')
        if name not in view_types:
            view_types.append(name)

    return view_types

def get_configured_jsonschema_types_for_plugin_view(view_type, resource):
    '''
    Returns a list of jsonschema type available for the views of a specific JSONSCHEMA_IVIEW plugin
    The view is retrieved by matching on the view_type and the plugin.info.name
    '''

    plugin = get_jsonschema_view_plugin(view_type)
    config = plugin.config
    return get_view_jsonshema_types(config, resource)

def get_view_info(view_type, resource):
    
    for plugin in _i.JSONSCHEMA_IVIEW_PLUGINS:
        info = plugin.info()
        if plugin.info().get('name') == view_type:
            return info


def resolve_view_body(view_id, args):
    
    resolve = args.get('resolve', 'false')
    wrap = args.get('wrap', 'false')
    view = _g.get_view(view_id)

    view_body = get_view_body(view)
    view_type = view.get('view_type')
    plugin = get_jsonschema_view_plugin(view_type)

    if not view_body:
        raise Exception(_('Unable to find a valid configuration for view ID: {}'.format(str(view.get('id')))))

    if wrap.lower() == 'true':
        view_body = plugin.wrap_view(view_body, view, args)

    if resolve.lower() == 'true':
        view_body = plugin.resolve(view_body, view, args)

    return view_body