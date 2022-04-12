
import json

import ckan.logic as logic
import ckan.plugins.toolkit as toolkit
import ckanext.jsonschema.logic.get as _g
import ckanext.jsonschema.interfaces as _i
from ckan.common import _, json, request

# import ckan.common as converters
# from paste.deploy.converters import asbool


# Define some shortcuts
NotFound = logic.NotFound
ValidationError = logic.ValidationError

# import ckanext.jsonschema.utils as _u
import logging
import traceback

import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.validators as _v
import ckanext.jsonschema.view_tools as _vt

log = logging.getLogger(__name__)

from flask import (Blueprint, Response, abort, jsonify, send_file,
                   stream_with_context)
from jinja2 import Markup, Template

# TODO decorate jsonschema blueprint with tools.initialize
jsonschema = Blueprint(_c.TYPE, __name__)


def importer_view():
    try:
        return toolkit.render('source/importer.html')
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, _('Harvest source not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, _('Unauthorized'))

jsonschema.add_url_rule(
    "/{}/importer".format(_c.TYPE),
    view_func=importer_view
)


def validate_view():
    try:
        return toolkit.render('source/validate.html')
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, _('Harvest source not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, _('Unauthorized'))

jsonschema.add_url_rule(
    "/{}/validate".format(_c.TYPE),
    view_func=validate_view
)


def clone_view():
    try:
        _t.initialize()
        return toolkit.render('source/clone.html')
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, _('Harvest source not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, _('Unauthorized'))

jsonschema.add_url_rule(
    "/{}/clone".format(_c.TYPE),
    view_func=clone_view
)

########################################

def read_schema(schema_type):
    '''
    Dumps the content of a local schema file.
    The file resolution is based on the configured schema folder and the (argument) json file name
    '''
    _t.initialize()
    return json.dumps(_t.get_schema_of(schema_type))

jsonschema.add_url_rule('{}/<path:schema_type>'.format(_c.REST_SCHEMA_PATH), view_func=read_schema, endpoint='schema', methods=[u'GET'])


def read_template(schema_type):
    '''
    Dumps the content of a local schema file.
    The file resolution is based on the configured schema folder and the (argument) json file name
    '''
    import os

    _t.initialize()
    return json.dumps(_t.get_template_of(schema_type))

jsonschema.add_url_rule('{}/<path:schema_type>'.format(_c.REST_TEMPLATE_PATH), view_func=read_template, endpoint='template', methods=[u'GET'])

def resolve_module(schema_type):
    '''
    Dumps the url of a js module file name matching the schema type
    '''
    
    _t.initialize()
    module = _t.get_module_for(schema_type)
    if module:
        return Response(stream_with_context(module), mimetype='application/javascript')
        #return send_file(module, mimetype='application/javascript')
    return abort(404, _('Unable to locate JS module for type: {}'.format(schema_type)))

jsonschema.add_url_rule('{}/<path:schema_type>'.format(_c.REST_MODULE_FILE_PATH), view_func=resolve_module, endpoint='module', methods=[u'GET'])


###### GET API

def get_body(dataset_id, resource_id = None):
    #return Response(stream_with_context(_t.get_body(dataset_id, resource_id)), mimetype='application/json')
    return Response(stream_with_context(json.dumps(_t.get_body(dataset_id, resource_id))), mimetype='application/json')

jsonschema.add_url_rule('/{}/body/<dataset_id>/<resource_id>'.format(_c.TYPE,), view_func=get_body, methods=[u'GET'])
jsonschema.add_url_rule('/{}/body/<dataset_id>'.format(_c.TYPE,), view_func=get_body, methods=[u'GET'])

def get_type(dataset_id, resource_id = None):
    return Response(stream_with_context(json.dumps(_t.get_type(dataset_id, resource_id))), mimetype='application/json')

jsonschema.add_url_rule('/{}/type/<dataset_id>/<resource_id>'.format(_c.TYPE), view_func=get_type, methods=[u'GET'])
jsonschema.add_url_rule('/{}/type/<dataset_id>'.format(_c.TYPE), view_func=get_type, methods=[u'GET'])

def get_opt(dataset_id, resource_id = None):
    return Response(stream_with_context(json.dumps(_t.get_opt(dataset_id, resource_id))), mimetype='application/json')

jsonschema.add_url_rule('/{}/opt/<dataset_id>/<resource_id>'.format(_c.TYPE), view_func=get_opt, methods=[u'GET'])
jsonschema.add_url_rule('/{}/opt/<dataset_id>'.format(_c.TYPE), view_func=get_opt, methods=[u'GET'])


# DUMP (#TODO package_show?)
def get_format(dataset_id, format = 'json'):

    try:
        body =_v.dataset_dump(dataset_id, format)

        # TODO MOVE ME
        _mimetype = 'application/json'
        if format == 'xml':
            _mimetype = 'application/xml'

        return Response(stream_with_context(body), mimetype=_mimetype)

    except toolkit.ObjectNotFound as e:
        return toolkit.abort(404, _("Dataset not found"))
    except Exception as e:
        return toolkit.abort(500, _(e.message))


jsonschema.add_url_rule('/{}/<dataset_id>.<format>'.format(_c.TYPE), view_func=get_format, methods=[u'GET'])


def get_registry_entry(jsonschema_type):
    entry =json.dumps(_t.get_from_registry(jsonschema_type))

    if entry:
        return Response(stream_with_context(entry), mimetype = 'application/json')
    else:
        return toolkit.abort(404, _('Entry not found for jsonschema_type: {}').format(jsonschema_type))
jsonschema.add_url_rule('/{}/registry/<path:jsonschema_type>'.format(_c.TYPE), view_func=get_registry_entry, methods=[u'GET'])


#from ckanext.jsonschema.logic.get import get_licenses_enum
#jsonschema.add_url_rule('/{}/core/schema/licenses.json'.format(_c.TYPE), view_func=get_licenses_enum, methods=[u'GET'])


############ VIEW



def get_view_body(package_id, resource_id, view_id):

    #from flask import redirect, url_for
    #return redirect(url_for('/'))


    try:
        resolve = request.args.get('resolve', 'false')
        wrap = request.args.get('wrap', 'false')
        view = _g.get_view(view_id)

        view_body = _vt.get_view_body(view)
        view_type = view.get('view_type')
        plugin = next(plugin for plugin in _i.JSONSCHEMA_IVIEW_PLUGINS if plugin.info().get('name') == view_type)

        if not view_body:
            raise Exception(_('Unable to find a valid configuration for view ID: {}'.format(str(view.get('id')))))

        if resolve.lower() == 'true':
            view_body = plugin.resolve(view_body, view)

        if wrap.lower() == 'true':
            view_body = plugin.wrap_view(view_type, view_body)
        
        return Response(stream_with_context(json.dumps(view_body)), mimetype='application/json')
    except ValidationError as e:
        traceback.print_exc()
        abort(400, e.error_dict.get('message'))
    except Exception as e:
        traceback.print_exc()
        abort(400, str(e))
    

def get_view_type(package_id, resource_id, view_id):
 
    view = _g.get_view(view_id)

    return Response(stream_with_context(json.dumps(_vt.get_view_type(view))), mimetype='application/json')


def get_view_opt(package_id, resource_id, view_id):

    view = _g.get_view(view_id)

    return Response(stream_with_context(json.dumps(_vt.get_view_opt(view))), mimetype='application/json')

jsonschema.add_url_rule('/{}/body/<package_id>/<resource_id>/<view_id>'.format(_c.TYPE), view_func=get_view_body, endpoint='get_view_body', methods=[u'GET'])
jsonschema.add_url_rule('/{}/type/<package_id>/<resource_id>/<view_id>'.format(_c.TYPE), view_func=get_view_type, methods=[u'GET'])
jsonschema.add_url_rule('/{}/opt/<package_id>/<resource_id>/<view_id>'.format(_c.TYPE), view_func=get_view_opt, methods=[u'GET'])


def get_model(package_id, resource_id):

    # TODO
    # This doesn't work
    # Define what has to be in the model    
    content = _vt._get_model(package_id, resource_id)


    return Response(stream_with_context(json.dumps(content)), mimetype='application/json')
jsonschema.add_url_rule('/{}/model/<package_id>/<resource_id>'.format(_c.TYPE), view_func=get_model, endpoint='model', methods=[u'GET'])

