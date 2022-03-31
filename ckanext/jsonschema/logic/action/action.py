# encoding: utf-8
import logging

import ckan.logic as logic
import ckan.plugins as plugins
from ckan.common import _

log = logging.getLogger(__name__)

# Define some shortcuts
# Ensure they are module-private so that they don't get loaded as available
# actions in the action API.
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError

import ckan.lib.navl.dictization_functions as df
import ckanext.jsonschema.configuration as configuration
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.validators as _v
from ckan.plugins import toolkit

StopOnError = df.StopOnError



@plugins.toolkit.chained_action
def resource_create(next_auth, context, data_dict):
    return validate_resource(next_auth, context, data_dict)


@plugins.toolkit.chained_action
def resource_update(next_auth, context, data_dict):
    return validate_resource(next_auth, context, data_dict)


def validate_resource(next_auth, context, data_dict):

    errors = {}
    key = ''

    try:
        body, _type, opt = _v.get_extras_from_resource(data_dict)
    except:
        # TODO 
        # should raise error if not jsonschema resource 
        return next_auth(context, data_dict)


    ######################### TODO #########################
    if opt.get('validation') == False:
        return

    if not _type:
        _v.stop_with_error('Unable to load a valid json schema type', key, errors)

    schema = _t.get_schema_of(_type)

    if not schema:
        _v.stop_with_error('Unable to load a valid json-schema for type {}'.format(_type), key, errors)

    is_error = _t.draft_validation(_type, body, errors)

    if is_error:
        raise ValidationError(df.unflatten(errors))

    extractor_context = {}

    extract_resource(data_dict, errors, extractor_context)

    return next_auth(context, data_dict)


def extract_resource(resource, errors, extractor_context):
    
    body, resource_type, opt = _v.get_extras_from_resource(resource)

    package = toolkit.get_action('package_show')({}, {'id': resource.get('package_id')})
    package_type = _t.get_dataset_type(package)

    if resource_type not in configuration.get_supported_resource_types(package_type):
        return          

    plugin = configuration.get_plugin(package_type, resource_type)
    
    extractor_context.update({
        _c.SCHEMA_BODY_KEY: body,
        _c.SCHEMA_TYPE_KEY : resource_type,
        _c.SCHEMA_OPT_KEY : opt,
    })

    try:
        extractor = plugin.get_resource_extractor(package_type, resource_type, extractor_context)
        extractor(resource, errors, extractor_context)
        #_t.update_extras_from_resource_context(resource, context)
        #data.update(df.flatten_dict(_data))

    except df.StopOnError:
        raise
    except Exception as e:
        raise ValidationError(df.unflatten(errors))
