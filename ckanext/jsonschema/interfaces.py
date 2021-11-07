from ckan.plugins.interfaces import Interface

class IBinder(Interface):

    def bind_with(self, body, opt, type, version):
        '''
        return true if this plugin can handle this type
        '''
        return False

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


    def extract_from_json(self, body, opt, type, version, key, data, errors, context):
        '''
        create the data model from the incoming body
        modify body in a UI suitable form
        it may match with the corresponding 'type' schema
        which is used by the jsonschema plugin to validate the
        incoming content (body) from API/UI
        '''
        pass

