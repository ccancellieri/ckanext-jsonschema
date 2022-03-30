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

StopOnError = df.StopOnError

def validate_resource(next_auth, context, data_dict):

    errors = {}
    key = ''

    body, _type, opt = _v.get_extras_from_resource(data_dict)
    
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

    return next_auth(context, data_dict)


@plugins.toolkit.chained_action
def resource_create(next_auth, context, data_dict):
    return validate_resource(next_auth, context, data_dict)


@plugins.toolkit.chained_action
def resource_update(next_auth, context, data_dict):
    return validate_resource(next_auth, context, data_dict)