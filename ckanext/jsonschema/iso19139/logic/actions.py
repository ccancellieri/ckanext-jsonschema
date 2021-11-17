from sqlalchemy.sql.operators import as_
from sqlalchemy.sql.sqltypes import ARRAY, TEXT
import ckan.plugins as plugins
import ckanext.terriajs.constants as constants

from ckan.model.resource_view import ResourceView
from ckan.model.resource import Resource
from ckan.model.package import Package
from ckan.model.core import State

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql.expression import cast
from sqlalchemy import func, Integer
from sqlalchemy.sql import select


import ckan.plugins.toolkit as toolkit
_ = toolkit._
h = toolkit.h


import ckan.logic as logic

_check_access = logic.check_access

#@plugins.toolkit.chained_action
def importer(context, data_dict):
    if not data_dict:
        error_msg = 'No dict provided'
        h.flash_error(error_msg,allow_html=True)
        return

    url = data_dict.get('url')
    if not url:
        h.flash_error(_('No url provided'), allow_html=True)
        return

    _check_access('package_create', context, data_dict)
    
    import requests
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        print("failed to fetch %s (code %s)" % (url,
                                                response.status_code))
        return


    import ckanext.jsonschema.utils as _u
    import ckanext.jsonschema.constants as _c

    package_dict={}
    # IMPORTER_TYPE = 'iso19139'
    _type = data_dict.get(_c.SCHEMA_TYPE_KEY)
    package_dict['type'] = _type
    package_dict['owner_org'] = data_dict.get('owner_org')

    import json
    extras = []
    package_dict['extras'] = extras
    extras.append({ 'key': _c.SCHEMA_BODY_KEY, 'value' : json.dumps(_u.xml_to_dict(response.text)) })
    extras.append({ 'key': _c.SCHEMA_TYPE_KEY, 'value' : _type })
    extras.append({ 'key': _c.SCHEMA_OPT_KEY, 'value' : json.dumps({'imported' : True}) })
    extras.append({ 'key': _c.SCHEMA_VERSION_KEY, 'value' : _c.SCHEMA_VERSION })    

    return toolkit.get_action('package_create')(context, package_dict)
    
    # next_action(context,data_dict)