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


    def extract_from_json(self, data, errors, context):
        '''
        create the data model from the incoming body
        modify body in a UI suitable form
        it may match with the corresponding 'type' schema
        which is used by the jsonschema plugin to validate the
        incoming content (body) from API/UI
        '''
        raise Exception('extract_from_json operation not supported for this format')

    def before_extractor(self, data, errors, context):
        '''
        Can be used as preprocessing step f.e. a transformation to a different jsonschema model
        '''
        raise Exception('before_extractor operation not supported for this format')

    def extract_id(self, body, type, opt, verion, errors, context):
        '''
        Returns the ID of this metadata extracted from the body
        Should be the same function used by name in extract_from_json
        '''
        pass

    def clone(self, package_dict, errors, context):
        '''
        Clones a package        
        '''
        raise Exception('clone operation not supported for this format')