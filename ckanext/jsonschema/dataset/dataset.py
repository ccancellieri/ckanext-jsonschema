import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
import uuid 

not_empty = toolkit.get_validator('not_empty')
is_boolean = toolkit.get_validator('boolean_validator')

import ckan.lib.navl.dictization_functions as df
import ckanext.jsonschema.dataset.constants as _dataset_constants

missing = df.missing
StopOnError = df.StopOnError
Invalid = df.Invalid

import logging

import ckanext.jsonschema.interfaces as _i

log = logging.getLogger(__name__)


#############################################


import ckan.lib.navl.dictization_functions as df

config = toolkit.config

def _extract_data_json_resource(data, errors, context):
    data.update({
        'format': 'JSON'
    })


supported_resource_types = {
    _dataset_constants.TYPE_DATASET_RESOURCE: _i.default_extractor,
    _dataset_constants.TYPE_JSON_RESOURCE: _extract_data_json_resource
}

def clone(source_pkg, package_dict, errors, context):

    for key, value in source_pkg.items():
        if key not in package_dict:
            package_dict[key] = value

    del package_dict['id']
    package_dict['name'] = str(uuid.uuid4())


clonable_package_types = {
    _dataset_constants.TYPE_DATASET: clone,
}


clonable_resources_types = {
    _dataset_constants.TYPE_DATASET_RESOURCE: _i.default_cloner,
    _dataset_constants.TYPE_JSON_RESOURCE: _i.default_cloner
}

class JsonschemaDataset(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(_i.IBinder, inherit = True)


    # IConfigurer
    def update_config(self, config_):
        pass
    

    def get_resource_extractor(self, package_type, resource_type, context):

        extractor_for_type = supported_resource_types.get(resource_type)

        if extractor_for_type:
            return extractor_for_type
        else:
            raise KeyError('Extractor not defined for package with type {}'.format(resource_type))


    def get_supported_resource_types(self):
        return supported_resource_types.keys()

    def get_clonable_resource_types(self):
        return clonable_resources_types.keys()

    def get_package_cloner(self, package_type):
        return clonable_package_types.get(package_type)

    def get_resource_cloner(self, package_type, resource_type):            
        return clonable_resources_types.get(resource_type)
