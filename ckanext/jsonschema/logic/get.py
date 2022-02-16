

import ckan.plugins.toolkit as toolkit
import ckan.logic as logic


# # TODO model
# class JsonSchema():

#     def __init__(self):
#         pass

    ## RESOURCE
    #   {% set extras = h.jsonschema_resolve_resource_extras(dataset_type, data) %}
    #     extras = {}
    #   {% set TYPE_KEY = h.jsonschema_get_type_key() %}
    #   {% set BODY_KEY = h.jsonschema_get_body_key() %}
    #   {% set OPT_KEY = h.jsonschema_get_opt_key() %}
    #   {% set VERSION_KEY = h.jsonschema_get_version_key() %}


    #   {% set schema_type = extras[TYPE_KEY] %}
    #   {% set body = extras[BODY_KEY] %}
    #   {% set opt = extras[OPT_KEY] %}
    #   {% set version = extras[VERSION_KEY] %}

    #   {% set schema = h.jsonschema_get_schema(schema_type) %}

    ### DATASET
    # {% if h.jsonschema_get_dataset_type() in h.jsonschema_handled_dataset_types() %}

    #   {% set extras = h.jsonschema_resolve_extras(data) %}

    #   {% set TYPE_KEY = h.jsonschema_get_type_key() %}
    #   {% set BODY_KEY = h.jsonschema_get_body_key() %}
    #   {% set OPT_KEY = h.jsonschema_get_opt_key() %}
    #   {% set VERSION_KEY = h.jsonschema_get_version_key() %}


    #   {% set schema_type = extras[TYPE_KEY] %}
    #   {% set body = extras[BODY_KEY] %}
    #   {% set opt = extras[OPT_KEY] %}
    #   {% set version = extras[VERSION_KEY] %}
    # body = {}

    #   {% set schema = h.jsonschema_get_schema(schema_type) %}
      

import ckanext.jsonschema.utils as _u
def get_pkg(dataset_id):
    '''
    Returns the model used by jinja2 template
    '''

    if not dataset_id:
        raise Exception('we expect a dataset_id')

    # may throw not found
    pkg = toolkit.get_action('package_show')(None, {'id':dataset_id})
    _pkg = _u.dictize_pkg(pkg)

    return _pkg

