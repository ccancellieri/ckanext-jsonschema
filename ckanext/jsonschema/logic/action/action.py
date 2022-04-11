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
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.validators as _v
from ckan.plugins import toolkit

StopOnError = df.StopOnError



@plugins.toolkit.chained_action
def resource_create(next_auth, context, data_dict):
    # We would like to do this, but...
    # Resources are different from packages. If we do this, jsonschema fields are flattened and clash with validatorsù
    # The input field [(u'resources', 4, u'jsonschema_body', 0, u'type'), ...] was not expected.

    # _v.jsonschema_resource_fields_to_json(data_dict)
    # result = validate_resource(next_auth, context, data_dict)
    # _v.jsonschema_resource_fields_to_string(data_dict)
    # return result
    return validate_resource(next_auth, context, data_dict)

@plugins.toolkit.chained_action
def resource_update(next_auth, context, data_dict):
    return validate_resource(next_auth, context, data_dict)

def validate_resource(next_auth, context, data_dict):

    errors = {}
    key = ''

    _type = _t.get_resource_type(data_dict)

    if not _type:
        # not a jsonschema resource, skip validation and extraction
        return next_auth(context, data_dict)

    body = _t.as_dict(_t.get_resource_body(data_dict))
    opt = _t.as_dict(_t.get_resource_opt(data_dict))

    package = toolkit.get_action('package_show')({}, {'id': data_dict.get('package_id')})
    package_type = _t.get_package_type(package)

    ######################### TODO #########################
    
    if opt.get('validation') == False:
        return
    ######################### #### #########################

    try:
        
        _v.item_validation(_type, body, opt, key, errors, context)

        _v.resource_extractor(data_dict, package_type, errors, context)

    except df.StopOnError:
        raise ValidationError(df.unflatten(errors))

    return next_auth(context, data_dict)
