import datetime

import ckan.plugins.toolkit as toolkit
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.utils as _u
import ckanext.jsonschema.validators as _v
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.configuration as configuration
import ckan.lib.navl.dictization_functions as df
from ckan.logic import NotFound, ValidationError
from ckan.plugins.core import PluginNotFoundException

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



    # CREATE EXTRAS
    _type = data_dict.get(_c.SCHEMA_TYPE_KEY)
    
    opt = dict(_c.SCHEMA_OPT)
    opt.update({
        'imported' : True,
        'source_format':'xml' if from_xml else 'json',
        'source_url': url,
        'imported_on': str(datetime.datetime.now())
    })


    # IMPORT - PREPROCESSING -
    import_context = {
        _c.SCHEMA_BODY_KEY: _t.as_dict(body),
        _c.SCHEMA_TYPE_KEY : _type,
        _c.SCHEMA_OPT_KEY : opt,
    }

    package_dict = {
        # IMPORTER_TYPE = 'iso19139'old
        'extras': _c.DEFAULT_EXTRAS, # initial extras
        'type': _type,
        'owner_org': data_dict.get('owner_org'),
        'license_id': data_dict.get('license_id')
    }

    errors = []

    try:
        plugin = configuration.get_plugin(_type)
    except PluginNotFoundException as e:
        return { "success": False, "msg": str(e)}

    extractor = plugin.get_input_extractor(_type, import_context) 
    extractor(package_dict, errors, import_context)   

    opt['validation'] = False  
    _t.update_extras_from_context(package_dict, import_context)


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

    

def validate_metadata(context, data_dict):

    id = data_dict.get('id')

    package = _t.get(id)

    if package is None:
        raise NotFound("No package found with the specified uuid")

    body = _t.get_dataset_body(package)
    _type = _t.get_dataset_type(package)
    
    errors = {}
    is_error = _t.draft_validation(_type, body, errors)
    
    if is_error:
        raise ValidationError(df.unflatten(errors))


def clone_metadata(context, data_dict):


    pkg = _t.get(data_dict.get('id'))

    _type = _t.get_dataset_type(pkg)
    body = _t.get_dataset_body(pkg)


    #jsonschema_extras = _t.remove_jsonschema_extras_from_package_data(pkg)

    package_dict = {
        'extras': pkg.get('extras'),
        'resources': [],
        'type': _type,
        'owner_org': data_dict.get('owner_org')
    }
    
    _check_access('package_create', context, package_dict)

    opt = {
        'cloned' : True,
        'source_url': pkg.get('url'),
        'cloned_on': str(datetime.datetime.now())
    }

    clone_context = {
        _c.SCHEMA_BODY_KEY: body,
        _c.SCHEMA_TYPE_KEY : _type,
        _c.SCHEMA_OPT_KEY : opt,
    }

    errors = []

    try:
        plugin = configuration.get_plugin(_type)
    except PluginNotFoundException as e:
        return { "success": False, "msg": str(e)}


    try:

        cloner = plugin.get_package_cloner(_type)

        if not cloner:
            message = 'No cloner configured for package type {}. Skipping'.format(_type)
            log.info(message)
            return { "success": False, "msg": message}

        
        cloner(package_dict, errors, clone_context)


        # Port back from context extras to data
        _t.update_extras_from_context(package_dict, clone_context)

        for resource in pkg.get('resources'):

            try:
                del resource['id']
                del resource['package_id']

                if 'revision_id' in resource:
                    del resource['revision_id']
                
                resource_clone_context = {
                    _c.SCHEMA_BODY_KEY: _t.get_resource_body(resource),
                    _c.SCHEMA_TYPE_KEY : _t.get_resource_type(resource),
                    _c.SCHEMA_OPT_KEY : _t.get_resource_opt(resource),
                }

                resource_type = _t.get_resource_type(resource)
                plugin = configuration.get_plugin(_type, resource_type)
                
                cloner = plugin.get_resource_cloner(_type, resource_type)

                if not cloner:
                    log.info('No cloner configured for resource type {} on package type {}. Skipping'.format(resource_type, _type))
                    continue
                
                cloner(resource, errors, resource_clone_context)

                _t.update_extras_from_resource_context(resource, resource_clone_context)

                # attach to package_dict
                package_dict['resources'].append(resource)
            except PluginNotFoundException: #TODO remove, should raise error
                pass 

        return toolkit.get_action('package_create')(context, package_dict)
    except Exception as e:
        import traceback
        traceback.print_exc()

        message = str(e)
        log.error(message)
        raise ValidationError(message)