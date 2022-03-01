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


    def get_before_extractor(self, package_type, context):
        '''
        Gets the before extractor for the specified type 
        Can be used as preprocessing step f.e. a transformation to a different jsonschema model
        If there isn't a before extractor for the type, should return None
        '''

        raise KeyError('Before extractor not implemented')
        

    def get_package_extractor(self, package_type, context):
        '''
        Gets the extractor for the specified package type 
        The extractor will create the data model from the incoming body in context

        The context is passed because some plugins (e.g. STAC) need to inspect the body to decide the extractor
        Could be removed?
        '''

        raise KeyError('get_package_extractor not implemented')


    def get_resource_extractor(self, package_type, resource_type):
        '''
        Gets the extractor for the specified resource type 
        The extractor will create the data model from the incoming body in context
        '''

        raise KeyError('get_resource_extractor not implemented')

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