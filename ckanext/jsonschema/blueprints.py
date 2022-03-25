
from ckan.logic import schema
from ckan.common import json
from ckan.plugins.toolkit import get_action, request, h, get_or_bust
import json

# import ckan.common as converters
# from paste.deploy.converters import asbool

import ckan.lib.helpers as h
import ckan.logic as logic
from ckan.model.package import Package
import ckan.plugins.toolkit as toolkit
from ckan.common import _, request

# Define some shortcuts
NotFound = logic.NotFound
ValidationError = logic.ValidationError

import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.validators as _v
# import ckanext.jsonschema.utils as _u
import logging
log = logging.getLogger(__name__)

from jinja2 import Template,Markup
from flask import Blueprint, abort, jsonify, send_file, Response, stream_with_context

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

jsonschema.add_url_rule('{}/<schema_type>'.format(_c.REST_TEMPLATE_PATH), view_func=read_template, endpoint='template', methods=[u'GET'])

def resolve_module(schema_type):
    '''
    Dumps the url of a js module file name matching the schema type
    '''
    import os

    _t.initialize()
    module = _t.get_module_for(schema_type)
    if module:
        # return Response(stream_with_context(module), mimetype='text/plain')
        return send_file(module, mimetype='application/javascript')
    return abort(404, _('Unable to locate JS module for type: {}'.format(schema_type)))

jsonschema.add_url_rule('{}/<schema_type>'.format(_c.REST_MODULE_FILE_PATH), view_func=resolve_module, endpoint='module', methods=[u'GET'])


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
jsonschema.add_url_rule('/{}/registry/<jsonschema_type>'.format(_c.TYPE), view_func=get_registry_entry, methods=[u'GET'])


#from ckanext.jsonschema.logic.get import get_licenses_enum
#jsonschema.add_url_rule('/{}/core/schema/licenses.json'.format(_c.TYPE), view_func=get_licenses_enum, methods=[u'GET'])
