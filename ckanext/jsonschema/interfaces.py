from ckan.plugins.interfaces import Interface

class IBinder(Interface):

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

    def dump_to_xml(self, body, type, key, version, data, context):
        '''
        serialize to body the data model in the desired form
        '''
        pass


    def extract_from_json(self, body, type, opt, version, key, data, errors, context):
        '''
        create the data model from the incoming body
        modify body in a UI suitable form
        it may match with the corresponding 'type' schema
        which is used by the jsonschema plugin to validate the
        incoming content (body) from API/UI
        '''
        pass

