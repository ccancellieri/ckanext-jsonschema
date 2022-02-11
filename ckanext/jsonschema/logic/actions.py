import datetime

import ckan.plugins.toolkit as toolkit
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.utils as _u
from ckan.logic import ValidationError

_ = toolkit._
h = toolkit.h

import logging

from paste.deploy.converters import asbool

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

    license_id = data_dict.get('license_id')
    if not license_id:
        h.flash_error(_('License is mandatory'), allow_html=True)
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
    package_dict['license_id'] = data_dict.get('license_id')
    
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
        # # TODO has deep impact/implications over resources
        is_package_update = asbool(data_dict.get('package_update', False))
        if is_package_update:
            # errors=[]
            # for plugin in _v.JSONSCHEMA_PLUGINS:
            #     if _type in plugin.supported_dataset_types(opt, _c.SCHEMA_VERSION):
            #         # _body = json.loads(body)
            #         _body = body
            #         id = plugin.extract_id(_body, _type, opt, _c.SCHEMA_VERSION, errors, context)
            #         if id:
            #             pkg = Package.get(id)
            #             if pkg and pkg.type == _type:
            #                 context["package"] = pkg
            #                 _dict={}
            #                 _dict["id"] = pkg.id
            #                 # _dict['type'] = pkg.type
            #                 _dict['extras'] = extras
            #                 return toolkit.get_action('package_update')(context, _dict)
            raise Exception('no support provided for this operation/format')
        else:
            return toolkit.get_action('package_create')(context, package_dict)
    except Exception as e:
        message = str(e)
        log.error(message)
        # e.error_summary = json.dumps(message)
        raise ValidationError(message)
    
    
    # next_action(context,data_dict)

    

