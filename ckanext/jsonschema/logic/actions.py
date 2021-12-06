import datetime

from sqlalchemy.sql.operators import as_
from sqlalchemy.sql.sqltypes import ARRAY, TEXT
from ckan.logic import ValidationError
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

import ckanext.jsonschema.utils as _u
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.validators as _v
import json

import ckan.plugins.toolkit as toolkit
_ = toolkit._
h = toolkit.h

from paste.deploy.converters import asbool

import logging
log = logging.getLogger(__name__)

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
    
    try:
        import requests
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            raise Exception('Unable to fetch data, response status is {}'.format(response.status_code))
    except Exception as e:
        message = str(e)
        log.error(message)
        # e.error_summary = json.dumps(message)
        raise ValidationError(message)

    # body is supposed to be json, if true a  1:1 conversion is provided
    from_xml = asbool(data_dict.get('from_xml', False))
    try:
        if from_xml:
            body = _u.xml_to_json(response.text)
        else:
            body = response.json() #TODO as json check 
    except Exception as e:
        message = str(e)
        log.error(message)
        # e.error_summary = json.dumps(message)
        raise ValidationError(message)

    package_dict={}
    # IMPORTER_TYPE = 'iso19139'old
    _type = data_dict.get(_c.SCHEMA_TYPE_KEY)
    package_dict['type'] = _type
    package_dict['owner_org'] = data_dict.get('owner_org')
    

    opt = dict(_c.SCHEMA_OPT)
    
    opt.update({
        'imported' : True,
        'source_format':'xml' if from_xml else 'json',
        'source_url': url,
        'imported_on': str(datetime.datetime.now())
        })
    extras = []
    package_dict['extras'] = extras
    extras.append({ 'key': _c.SCHEMA_BODY_KEY, 'value' : body })
    extras.append({ 'key': _c.SCHEMA_TYPE_KEY, 'value' : _type })
    extras.append({ 'key': _c.SCHEMA_OPT_KEY, 'value' :  opt })
    extras.append({ 'key': _c.SCHEMA_VERSION_KEY, 'value' : _c.SCHEMA_VERSION })

    #TODO resources store back to the package_dict
    try:
        is_package_update = asbool(data_dict.get('package_update', False))
        if is_package_update:
            errors=[]
            for plugin in _v.JSONSCHEMA_PLUGINS:
                if _type in plugin.supported_dataset_types(opt, _c.SCHEMA_VERSION):
                    id = plugin.extract_id(json.loads(body), _type, opt, _c.SCHEMA_VERSION, errors, context)
                    if id:
                        package_dict['id'] = id
                        return toolkit.get_action('package_update')(context, package_dict)
            raise Exception('no rupport provided for this operation/format')
        else:
            return toolkit.get_action('package_create')(context, package_dict)
    except Exception as e:
        message = str(e)
        log.error(message)
        # e.error_summary = json.dumps(message)
        raise ValidationError(message)
    
    
    # next_action(context,data_dict)