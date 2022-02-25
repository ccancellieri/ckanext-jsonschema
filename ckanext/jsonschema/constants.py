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
SCHEMA_OPT_KEY='jsonschema_opt'
SCHEMA_OPT={} # TODO MAKE DEFAULT CONFIG CONFIGURABLE....
SCHEMA_BODY_KEY='jsonschema_body'
# to mark a metadata as 
# ckanext-jsonschema managed package
SCHEMA_VERSION_KEY='jsonschema_version'
SCHEMA_VERSION=1 # TODO MAKE DEFAULT VERSION CONFIGURABLE....
# TODO schema Mapping
SCHEMA_TYPE_KEY='jsonschema_type'

# (Optional)
# List of formats supported 
# ckanext.jsonschema.dataset.formats = []
SUPPORTED_DATASET_FORMATS = config.get('ckanext.jsonschema.dataset.formats', ['jsonschema'])
if isinstance(SUPPORTED_DATASET_FORMATS,str):
   # log.debug("DEFAULT_FORMATS is still a string: {}".format(PATH_SCHEMA))
   DEFAULT_FORMATS = json.loads(SUPPORTED_DATASET_FORMATS)
if not isinstance(SUPPORTED_DATASET_FORMATS,list):
   raise Exception('SUPPORTED_DATASET_FORMATS should be an array of valid format strings')

# (Optional)
# List of formats supported 
# ckanext.jsonschema.dataset.formats = []
SUPPORTED_RESOURCE_FORMATS = config.get('ckanext.jsonschema.resource.formats', ['resource-dataset'])
if isinstance(SUPPORTED_RESOURCE_FORMATS,str):
   # log.debug("DEFAULT_FORMATS is still a string: {}".format(PATH_SCHEMA))
   SUPPORTED_RESOURCE_FORMATS = json.loads(SUPPORTED_RESOURCE_FORMATS)
if not isinstance(SUPPORTED_RESOURCE_FORMATS,list):
   raise Exception('SUPPORTED_RESOURCE_FORMATS should be an array of valid format strings')


# (Internal)
##############################
# (Internal)
#  Will contain the schema and template defined with the type-mapping
JSON_SCHEMA_KEY = 'schema'
JSON_TEMPLATE_KEY = 'template'
JSON_CONFIG_KEY = 'config'
JSONSCHEMA_CONFIG = {}
JS_MODULE_KEY = 'module'
JSON_CATALOG = {
   JSON_SCHEMA_KEY: {},
   JSON_TEMPLATE_KEY: {},
   JS_MODULE_KEY: {},
   JSON_CONFIG_KEY: {}
}
JSON_CATALOG_INITIALIZED = False
#############################

# (Optional)
# fields to do not interpolate with jinja2 (f.e. they are a template of other type)
# FIELDS_TO_SKIP = config.get('ckanext.jsonschema.skip.fields', ['featureInfoTemplate'])

# (Optional)
# SERVER LOCAL PATH FOLDER WHERE JSON-SCHEMA are located.
PATH_SCHEMA=path.realpath(config.get('ckanext.jsonschema.path.schema', path.join(PATH_ROOT,'schema')))
PATH_CORE_SCHEMA='core'
REST_SCHEMA_PATH='/{}/schema'.format(TYPE)
REST_SCHEMA_FILE_PATH='/{}/schema_file'.format(TYPE)


# (Optional)
# Used as jinja template to initialize the items values, it's name is by convention the type
# same type may also be located under mapping
PATH_TEMPLATE=path.realpath(config.get('ckanext.jsonschema.path.template', path.join(PATH_ROOT,'template')))
REST_TEMPLATE_PATH='/{}/template'.format(TYPE)

#REST_GET_BODY = TODO
REST_GET_BODY_PATH='/{}/body'.format(TYPE)


# (Optional)
# Used as options
PATH_OPT=path.realpath(config.get('ckanext.jsonschema.path.opt', path.join(PATH_ROOT,'opt')))
REST_OPT_PATH='/{}/opt'.format(TYPE)

# (Optional)
# Used as json-editor modules to initialize the UI with js extension points
PATH_MODULE=path.realpath(config.get('ckanext.jsonschema.path.moudle', path.join(PATH_ROOT,'module')))
REST_MODULE_FILE_PATH='/{}/module'.format(TYPE)

PATH_CONFIG=path.realpath(config.get('ckanext.jsonschema.path.config', path.join(PATH_ROOT,'config')))
