from ckan.plugins.interfaces import Interface

class IBinder(Interface):

    # def opt_map(self, dataset_type, opt, version):
    #     ''''
    #     returns a map of options (by type)
    #     Each option will be passed as RUNTIME option
    #     This is used by json-schema to pass js functions
    #     to enrich the jsonschema editor capabilities with 
    #     autocompletion and much more.
    #     NOTE: thise opt map will not be stored into the metadata

    #     '''
    #     return opt
    def supported_output_types(self, dataset_type, opt, version):
        return []

    def supported_resource_types(self, dataset_type, opt, version):
        '''
        returns a list of supported resource type
        '''
        return [] #'dataset'

    def supported_dataset_types(self, opt, version):
        '''
        returns a list of supported resource type
        '''
        return [] #'dataset'

    def dump_to_json(self, body, type, version, key, data, context):
        '''
        return a serialized version in the desired profile of the data model
        '''
        # TODO jinja2 template body as model ?
        pass

    def dump_to_output(self, body, type, opt, version, data, output_format, context):
        '''
        serialize to body the data model in the desired form
        '''
        pass


    def extract_from_json(self, body, type, opt, version, data, errors, context):
        '''
        create the data model from the incoming body
        modify body in a UI suitable form
        it may match with the corresponding 'type' schema
        which is used by the jsonschema plugin to validate the
        incoming content (body) from API/UI
        '''
        return body, type, opt, version, data

    def before_extractor(self, body, type, opt, version, data, errors, context):
        '''
        Can be used as preprocessing step f.e. a transformation to a different jsonschema model
        '''
        return body, type, opt, version, data

    def extract_id(self, body, type, opt, verion, errors, context):
        '''
        Returns the ID of this metadata extracted from the body
        Should be the same function used by name in extract_from_json
        '''
        pass

