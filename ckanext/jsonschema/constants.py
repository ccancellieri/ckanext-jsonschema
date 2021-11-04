# from sqlalchemy.sql.expression import true
import ckan.plugins.toolkit as toolkit
config = toolkit.config
import json
import os
path = os.path
PATH_ROOT=path.realpath(path.join(path.dirname(__file__),'..'))
##############################

# (Internal)
# the name of the plugin
TYPE='jsonschema'

# Schema keys will be part of the extras keys
SCHEMA_OPT_KEY='_opt_'
SCHEMA_BODY_KEY='_body_'
# to mark a metadata as 
# ckanext-jsonschema managed package
SCHEMA_VERSION_KEY='_version_'
SCHEMA_VERSION='0.1'
# TODO schema Mapping
SCHEMA_TYPE_KEY='_type_'

# (Internal)
##############################
# (Internal)
#  Will contain the schema and template defined with the type-mapping
JSON_SCHEMA_KEY = 'schema'
JSON_TEMPLATE_KEY = 'template'
JSON_CATALOG = {
   JSON_SCHEMA_KEY: {},
   JSON_TEMPLATE_KEY: {}
}

#############################

# (Optional)
# fields to do not interpolate with jinja2 (f.e. they are a template of other type)
# FIELDS_TO_SKIP = config.get('ckanext.jsonschema.skip.fields', ['featureInfoTemplate'])

# (Optional)
# SERVER LOCAL PATH FOLDER WHERE JSON-SCHEMA are located.
PATH_SCHEMA=path.realpath(config.get('ckanext.jsonschema.path.schema', path.join(PATH_ROOT,'schema')))

# (Optional)
# Used as jinja template to initialize the items values, it's name is by convention the type
# same type may also be located under mapping
PATH_TEMPLATE=path.realpath(config.get('ckanext.jsonschema.path.template', path.join(PATH_ROOT,'template')))

# REST paths
REST_MAPPING_PATH='/{}/mapping'.format(TYPE)
REST_SCHEMA_PATH='/{}/schema'.format(TYPE)
# TODO REST_*_PATH
# document PAGE_SIZE
PAGE_SIZE = 15




