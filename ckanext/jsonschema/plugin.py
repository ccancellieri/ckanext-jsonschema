import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckan.common import c

_ = toolkit._


import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.validators as _v

get_validator = toolkit.get_validator
not_missing = get_validator('not_missing')
not_empty = get_validator('not_empty')
resource_id_exists = get_validator('resource_id_exists')
package_id_exists = get_validator('package_id_exists')
ignore_missing = get_validator('ignore_missing')
empty = get_validator('empty')
boolean_validator = get_validator('boolean_validator')
int_validator = get_validator('int_validator')
OneOf = get_validator('OneOf')

convert_to_extras = toolkit.get_converter('convert_to_extras')
convert_from_extras = toolkit.get_converter('convert_from_extras')

    # let's grab the default schema in our plugin
from ckan.logic.schema import \
    default_create_package_schema,\
    default_update_package_schema,\
    default_group_schema,\
    default_tags_schema

class JsonschemaPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)


    # IPackageController

    def before_index(self, pkg_dict):
        '''
        Extensions will receive what will be given to the solr for indexing. This is essentially a flattened dict (except for multli-valued fields such as tags) of all the terms sent to the indexer. The extension can modify this by returning an altered version.
        '''
        # TODO solr
        pass

    # def before_view(self, pkg_dict):
    #     '''
    #     Extensions will recieve this before the dataset
    #     gets displayed. The dictionary passed will be
    #     the one that gets sent to the template.
    #     '''
    #     pass

    # ITemplateHelpers

    def get_helpers(self):
        return {
                'is_jsonschema': lambda : True,
                'package_types': self.package_types,
                'get_body_key': lambda : _c.SCHEMA_BODY_KEY,
                'get_type_key': lambda : _c.SCHEMA_TYPE_KEY,
                'get_opt_key': lambda : _c.SCHEMA_OPT_KEY,
                'get_version_key': lambda : _c.SCHEMA_VERSION_KEY,
                'get_schema': _t.get_schema_of,
                'get_template': _t.get_template_of
        }

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'jsonschema')

        # Append all the rest of the available schemas
        _c.JSON_CATALOG.update({
                    _c.JSON_SCHEMA_KEY:_t.read_all_schema(),
                    _c.JSON_TEMPLATE_KEY:_t.read_all_template()
            })

        assert len(_c.JSON_CATALOG[_c.JSON_SCHEMA_KEY])==\
            len(_c.JSON_CATALOG[_c.JSON_TEMPLATE_KEY])
    

        # namespaces = {u'http://www.opengis.net/gml/3.2': u'gml', u'http://www.isotc211.org/2005/srv': u'srv', u'http://www.isotc211.org/2005/gts': u'gts', u'http://www.isotc211.org/2005/gmx': u'gmx', u'http://www.isotc211.org/2005/gmd': u'gmd', u'http://www.isotc211.org/2005/gsr': u'gsr', u'http://www.w3.org/2001/XMLSchema-instance': u'xsi', u'http://www.isotc211.org/2005/gco': u'gco', u'http://www.isotc211.org/2005/gmi': u'gmi', u'http://www.w3.org/1999/xlink': u'xlink'}
        # # TODO DEBUG
        # import ckanext.jsonschema.utils as _u
        # import os
        # j = _u.xml_to_json_from_file(os.path.join(_c.PATH_TEMPLATE,'test_iso.xml'))
        # import json
        # _j=json.loads(j)
        # _namespaces=_j['http://www.isotc211.org/2005/gmd:MD_Metadata']['@xmlns']
        # namespaces = dict((v,k) for k,v in _namespaces.iteritems())
        # _u.json_to_xml()
        # _u.xml_to_json_from_file(os.path.join(_c.PATH_TEMPLATE,'test_iso.xml'), True, namespaces)
        
    # IValidators

    def get_validators(self):

        '''
        Validators that need access to the database or information 
        about the user may be written as a callable taking two 
        parameters. context['session'] is the sqlalchemy session 
        object and context['user'] is the username of the logged-in 
        user:

        from ckan.plugins.toolkit import Invalid

        validator(key, flattened_data, errors, context)

        Validators that need to access or update multiple fields 
        may be written as a callable taking four parameters.

        All fields and errors in a flattened form are passed to 
        the validator. The validator must fetch values from 
        flattened_data and may replace values in flattened_data. 
        The return value from this function is ignored.

        key is the flattened key for the field to which this 
        validator was applied. For example ('notes',) for the 
        dataset notes field or ('resources', 0, 'url') for the 
        url of the first resource of the dataset. These flattened 
        keys are the same in both the flattened_data and errors 
        dicts passed.

        errors contains lists of validation errors for each field.

        context is the same value passed to the two-parameter 
        form above.

        Note that this form can be tricky to use because some 
        of the values in flattened_data will have had validators 
        applied but other fields won't. You may add this type of 
        validator to the special schema fields __before or 
        __after to have them run before or after all the other 
        validation takes place to avoid the problem of working 
        with partially-validated data.
        '''

        return {
            # u'equals_to_zero': lambda x : x==0,
            u'schema_is_valid': _v.schema_check,
        }

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return False

    def package_types(self):
        '''
        The package_types() function defines a list of dataset types that
        this plugin handles. Each dataset has a field containing its type.
        Plugins can register to handle specific types of dataset and ignore
        others. Since our plugin is not for any specific type of dataset and
        we want our plugin to be the default handler, we update the plugin
        code to contain the following:
        '''
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).

        return _c.JSON_CATALOG[_c.JSON_SCHEMA_KEY].keys()

    # IDatasetForm
    ##############

    def setup_template_variables(self, context, data_dict):
        
        # super(toolkit.DefaultDatasetForm,self).setup_template_variables(self, context, data_dict)
        
        # TODO: https://github.com/ckan/ckan/issues/6518
        path = c.environ['CKAN_CURRENT_URL']
        type = path.split('/')[1]

        
        # data_dict.update({
        #     _c.SCHEMA_VERSION_KEY : _c.SCHEMA_VERSION
        # })
        jsonschema = {
            # 'data_dict' : data_dict,
            _c.SCHEMA_TYPE_KEY : type,
            _c.SCHEMA_VERSION_KEY : _c.SCHEMA_VERSION
        }
        c.jsonschema = jsonschema

        return jsonschema

    # def new_template(self):
    #     return 'package/new.html'

    # def read_template(self):
    #     return 'package/read.html'

    # def edit_template(self):
    #     return 'package/edit.html'

    # def search_template(self):
    #     return 'package/search.html'

    # def history_template(self):
    #     return 'package/history.html'

    # def resource_template(self):
    #     return 'package/resource_read.html'

    # def package_form(self):
    #     return 'package/new_package_form.html'

    # def resource_form(self):
    #     return 'package/snippets/resource_form.html'

    # Updating the CKAN schema
    def create_package_schema(self):
        '''
        The create_package_schema() function is used whenever
        a new dataset is created, we'll want update the default 
        schema and insert our custom field here. 
        We will fetch the default schema defined in default_create_package_schema() 
        by running create_package_schema()'s super function and update it.
        '''

        # schema = super(toolkit.DefaultDatasetForm, self).create_package_schema()
        schema = default_create_package_schema()

        return self._modify_package_schema(schema)

    def update_package_schema(self):
        '''
        The CKAN schema is a dictionary where the key is the name of the field
        and the value is a list of validators and converters.
        Here we have a validator to tell CKAN to not raise a validation error if
        the value is missing and a converter to convert the value to and save
        as an extra. 
        We will want to change the update_package_schema() function with the
        same update code.
        '''
        schema = default_update_package_schema()

        return self._modify_package_schema(schema)

    def show_package_schema(self):
        '''
        The show_package_schema() is used when the package_show() action is 
        called, we want the default_show_package_schema to be updated to 
        include our custom field. 
        This time, instead of converting to an extras field, we want our 
        field to be converted from an extras field.
        So we want to use the convert_from_extras() converter.
        '''
        schema = default_create_package_schema()

        schema.update({
            _c.SCHEMA_OPT_KEY : [ convert_from_extras, ignore_missing ],
            _c.SCHEMA_BODY_KEY: [ convert_from_extras ],
            _c.SCHEMA_TYPE_KEY: [ convert_from_extras ],
            _c.SCHEMA_VERSION_KEY: [ convert_from_extras, _v.default_version ]
        })
                # Add our custom_resource_text metadata field to the schema
        schema['resources'].update({
                _c.SCHEMA_BODY_KEY : [ convert_from_extras, ignore_missing ],
                _c.SCHEMA_TYPE_KEY: [ convert_from_extras ],
                _c.SCHEMA_VERSION_KEY: [ convert_from_extras, _v.default_version ]
                })
        return schema
        
    def _modify_package_schema(self, schema):
        # our custom field
        # not_missing, not_empty, resource_id_exists, package_id_exists, 
        # ignore_missing, empty, boolean_validator, int_validator,  OneOf
        schema.update({
            _c.SCHEMA_OPT_KEY : [ ignore_missing, convert_to_extras ],
            _c.SCHEMA_BODY_KEY: [ not_missing, _v.schema_check, convert_to_extras ],
            _c.SCHEMA_TYPE_KEY: [ not_missing, convert_to_extras ],
            _c.SCHEMA_VERSION_KEY: [ _v.default_version, convert_to_extras ]
        })
        # Add our custom_resource_text metadata field to the schema
        schema['resources'].update({
                _c.SCHEMA_BODY_KEY : [ not_missing, _v.schema_check, convert_to_extras ],
                _c.SCHEMA_TYPE_KEY: [ not_missing, convert_to_extras ],
                _c.SCHEMA_VERSION_KEY: [ _v.default_version, convert_to_extras ]
                })
        return schema

    