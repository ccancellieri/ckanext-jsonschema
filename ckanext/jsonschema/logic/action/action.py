# encoding: utf-8
from ckan.lib.search import SearchIndexError
import ckan.model.domain_object as domain_object
from ckan.plugins import toolkit
import ckanext.jsonschema.validators as _v
import ckanext.jsonschema.tools as _t
import ckan.model as model
import ckan.lib.navl.dictization_functions as df
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

    package = toolkit.get_action('package_show')(
        context, {'id': data_dict.get('package_id')})
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


@plugins.toolkit.chained_action
def resource_view_update(next_auth, context, data_dict):
    next = next_auth(context, data_dict)
    if not context.get('prevent_notify'):
        index_package(data_dict)
    return next


@plugins.toolkit.chained_action
def resource_view_create(next_auth, context, data_dict):
    next = next_auth(context, data_dict)
    if not context.get('prevent_notify'):
        index_package(data_dict)
    return next


@plugins.toolkit.chained_action
def resource_view_delete(next_auth, context, data_dict):
    if not context.get('prevent_notify'):
        index_package(data_dict)
    return next_auth(context, data_dict)


def index_package(data_dict):

    package_id = data_dict.get('package_id')

    if not package_id:
        if 'id' in data_dict:  # this is the view id
            try:
                resource_view = toolkit.get_action('resource_view_show')(
                    None, {u'id': data_dict.get('id')})
                package_id = resource_view.get('package_id')
            except:
                log.error(
                    'Unable to locate the resource for view id: {}'.data_dict.get('id'))
                pass
        elif 'resource_id' in data_dict:
            try:
                resource = toolkit.get_action('resource_show')(
                    None, {u'id': data_dict.get('resource_id')})
                package_id = resource.get('package_id')
            except:
                log.error('Unable to locate the package for resource id: {}'.data_dict.get(
                    'resource_id'))
                pass

    if not package_id:
        log.error(
            'Aborting: Unable to reindex the package for view id: {}'.data_dict.get('id'))
        return

    package = model.Package.get(package_id)

    # code from ckan/model/modification
    for observer in plugins.PluginImplementations(plugins.IDomainObjectModification):
        try:
            observer.notify(
                package, domain_object.DomainObjectOperation.changed)
        except SearchIndexError as search_error:
            log.exception(search_error)
            # Reraise, since it's pretty crucial to ckan if it can't index
            # a dataset
            raise
        except Exception as ex:
            log.exception(ex)
            # Don't reraise other exceptions since they are generally of
            # secondary importance so shouldn't disrupt the commit.
