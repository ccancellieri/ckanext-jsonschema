import ckan.plugins.toolkit as toolkit
from ckan.logic import ValidationError

_ = toolkit._
import json
import logging

import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.logic.get as _g
from ckan.plugins.toolkit import get_or_bust, h
from ckanext.jsonschema.interfaces import JSONSCHEMA_IVIEW_PLUGINS


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


def get_interpolated_view_model(resource_view_id):

    view = _g.get_view(resource_view_id)
    
    if not view:
        raise Exception(_('No view found for view_id: {}'.format(str(resource_view_id))))

    view_body = get_view_body(view)
    if not view_body:
        raise Exception(_('Unable to find a valid configuration for view ID: {}'.format(str(resource_view_id))))

    view_type = view.get("view_type") 

    model = _get_model(dataset_id=get_or_bust(view,'package_id'), resource_id=get_or_bust(view,'resource_id'))
    
    return interpolate_fields(model, view_body, view_type)

def _get_model(dataset_id, resource_id):
    '''
    Returns the model used by jinja2 template
    '''

    if not dataset_id or not resource_id:
        raise Exception('wrong parameters we expect a dataset_id and a resource_id')

    # TODO can we have a context instead of None?
    pkg = toolkit.get_action('package_show')(None, {'id':dataset_id})
    if not pkg:
        raise Exception('Unable to find dataset, check input params')

    pkg = _t.dictize_pkg(pkg)

    # res = filter(lambda r: r['id'] == view.resource_id,pkg['resources'])[0]
    res = next(r for r in pkg['resources'] if r['id'] == resource_id)
    if not res:
        raise Exception('Unable to find resource under this dataset, check input params')

    # return the model as dict
    _dict = {
        'dataset': pkg,
        'organization': get_or_bust(pkg,'organization'),
        'resource':res,
        'ckan':{'base_url':h.url_for('/', _external=True)},
        #'data': {} #TODO
        #'terriajs':{'base_url': _c.TERRIAJS_URL}
        }

    return _dict 

def _load_resource_content_from_disk(resource):
    import json

    import ckan.lib.uploader as uploader

    upload = uploader.get_resource_uploader(resource)
    filepath = upload.get_path(resource['id'])

    with open(filepath) as f:
        resource_content = json.loads(f.read())
    
    return resource_content


def _enhance_model_with_data_helpers(model, view_type):
    '''
    This methods adds data helpers from plugins to the model provided to the template renderer
    Plugins implementing the IJsonschemaView interface can define the method get_data_helpers which returns a list of function
    The function are injected with their name in the environment of jinja
    '''

    resource_content = get_resource_content(model['resource'])
    
    # get the plugin that manages the view; should always be just one
    plugin = next(plugin for plugin in JSONSCHEMA_IVIEW_PLUGINS if plugin.info().get('name') == view_type)
    data_helpers = plugin.get_data_helpers(resource_content)

    # TODO CHECK FOR CONFLICTS
    model.update(data_helpers)


def get_resource_content(resource):

    # TODO understand resource type jsonschema, url, localfile
            # TODO schema validation in case of url or localfile
    # TODO query resource options for customized logic on where to pick up data
    # if jsonschema
    # resource_content = json.loads(_t.get_resource_body(resource_body))
    # else load from disk
    is_jsonschema = _t.get_resource_type(resource) != None
    is_upload = resource.get('url_type') == 'upload'

    if is_jsonschema:
        resource_content = _t.get_resource_body(resource)
    elif is_upload:
        resource_content = _load_resource_content_from_disk(resource)

    return resource_content

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

    _enhance_model_with_data_helpers(model, view_type)
    
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