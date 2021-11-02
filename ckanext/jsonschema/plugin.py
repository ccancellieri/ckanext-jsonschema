import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


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
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)

    # ITemplateHelpers

    def get_helpers(self):
        return {'key': 'value'}

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'jsonschema')
    
    def configure(self, config_):
        # Append all the rest of the available schemas
        _c.JSON_CATALOG.update({
                _c.JSON_SCHEMA_KEY:_t.read_all_schema(),
                _c.JSON_TEMPLATE_KEY:_t.read_all_template()
            })

        assert len(_c.JSON_CATALOG[_c.JSON_SCHEMA_KEY])==\
            len(_c.JSON_CATALOG[_c.JSON_TEMPLATE_KEY])

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
        applied but other fields won’t. You may add this type of 
        validator to the special schema fields '__before' or 
        '__after' to have them run before or after all the other 
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
        return True

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

    # Updating the CKAN schema
    def create_package_schema(self):
        '''
        The create_package_schema() function is used whenever
        a new dataset is created, we’ll want update the default 
        schema and insert our custom field here. 
        We will fetch the default schema defined in default_create_package_schema() 
        by running create_package_schema()’s super function and update it.
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
            _c.SCHEMA_OPT_KEY : [ ignore_missing, convert_from_extras ],
            _c.SCHEMA_BODY_KEY: [ convert_from_extras ],
            _c.SCHEMA_TYPE_KEY: [ convert_from_extras ],
            _c.SCHEMA_VERSION_KEY: [ convert_from_extras ]
        })
        return schema
        
    def _modify_package_schema(self, schema):
        # our custom field
        # not_missing, not_empty, resource_id_exists, package_id_exists, 
        # ignore_missing, empty, boolean_validator, int_validator,  OneOf
        schema.update({
            _c.SCHEMA_OPT_KEY : [ ignore_missing ],
            _c.SCHEMA_BODY_KEY: [ not_missing, convert_to_extras ],
            _c.SCHEMA_TYPE_KEY: [ not_missing, convert_to_extras ],
            _c.SCHEMA_VERSION_KEY: [ not_missing, convert_to_extras ]
        })
        # Add our custom_resource_text metadata field to the schema
        schema['resources'].update({
                _c.SCHEMA_BODY_KEY : [ ignore_missing ],
                _c.SCHEMA_TYPE_KEY: [ ignore_missing ],
                _c.SCHEMA_VERSION_KEY: [ not_missing, convert_to_extras ]
                })
        return schema

    