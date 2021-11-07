
from ckan.common import json
from ckan.plugins.toolkit import get_action, request, h, get_or_bust
import json

# import ckan.common as converters
# from paste.deploy.converters import asbool

import ckan.lib.helpers as h
import ckan.logic as logic
import ckan.plugins.toolkit as toolkit
from ckan.common import _, request

# Define some shortcuts
NotFound = logic.NotFound
ValidationError = logic.ValidationError

import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
# import ckanext.terriajs.utils as utils
import logging
log = logging.getLogger(__name__)

from jinja2 import Template,Markup
from flask import Blueprint, abort, jsonify

jsonschema = Blueprint(_c.TYPE, __name__)
#url_prefix=constants.TYPE)

########################################
## Schema proxy

def read_schema(filename):
    '''
    Dumps the content of a local schema file.
    The file resolution is based on the configured schema folder and the (argument) json file name
    '''
    import os
    return json.dumps(_t.get_schema_of(os.path.splitext(filename)[0]))

jsonschema.add_url_rule('{}/<filename>'.format(_c.REST_SCHEMA_PATH), view_func=read_schema, endpoint='schema', methods=[u'GET'])
