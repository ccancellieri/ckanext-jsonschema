from ckan.plugins.interfaces import Interface
from ckan.plugins import PluginImplementations


class IJsonschemaView(Interface):
    
    def register_jsonschema_resources(self):
        '''
        Use this method to register schemas, template, module to jsonschema's catalog
        '''
        
        pass


    def get_model(self, view):
        """
        Optionally used in resolve if needed
        Plugins can enrich the model

        Needed because interpolate already has the view, while the blueprint only has the view_id
        This method retrieves the id and calls _get_model which expects the view and not the id
        """
        import ckanext.jsonschema.view_tools as _vt
        return _vt.get_model(view.get('package_id'), view.get('resource_id'))

    def resolve(self, template):
        return template

    def wrap_view(self, view_body, view):
        return view_body

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

    def register_jsonschema_resources():
        '''
        Use this method to register schemas, template, module to jsonschema's catalog
        '''
        
        pass

    def dump_to_json(self, body, type, key, data, context):
        '''
        return a serialized version in the desired profile of the data model
        '''
        # TODO jinja2 template body as model ?
        pass

    def dump_to_output(self, data, errors, context, output_format):
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
        return lambda data, errors, context : None
        

    def get_resource_extractor(self, package_type, resource_type):
        '''
        Gets the extractor for the specified resource type 
        The extractor will create the data model from the incoming body in context
        '''

        raise NotImplementedError('get_resource_extractor not implemented')

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
        raise NotImplementedError('clone operation not supported for this format')

    
    def get_input_types(self):
        ''' 
        Returns the input types managed from the plugin
        Could be implemented returning the keys of a map {type: extractor_function_for_type}
        '''

        return []

    def get_supported_types(self):
        ''' 
        Returns the supported types managed from the plugin
        Could be implemented returning the keys of a map {type: extractor_function_for_type}
        '''

        return []

    def get_supported_resource_types(self):
        ''' 
        Returns the supported resource types managed from the plugin
        Could be implemented returning the keys of a map {type: extractor_function_for_type}
        '''

        return []

    def get_clonable_resource_types(self):
        ''' 
        Returns clonable resource types managed from the plugin
        Could be implemented returning the keys of a map {type: extractor_function_for_type}
        '''
        
        return []
        
    def get_input_extractor(self, package_type, package_dict, context):
        ''' 
        Returns input extractor function for the package type
        '''
        
        return None
    

    def get_package_extractor(self, package_type, package_dict, context):
        ''' 
        Gets the extractor for the specified package type 
        The extractor will create the data model from the incoming body in context

        The package_dict is passed because some plugins (e.g. STAC) need to inspect the body to decide the extractor
        Could be removed?
        '''

        raise NotImplementedError('get_package_extractor not implemented')


    def get_resource_extractor(self, package_type, resource_type, context):
        ''' 
        Returns extractor function for the resource type
        '''
        
        return None

    def get_package_cloner(self, package_type):
        ''' 
        Returns cloner extractor function for the package type
        '''
        return None

    def get_resource_cloner(self, package_type, resource_type):            
        ''' 
        Returns cloner extractor function for the resource type
        '''
        return None

    def get_dump_to_output(self, package_type):            
        ''' 
        Returns dump function for the package_type
        '''
        return None

    def get_model(self, package_id, resource_id):
        '''
        Optionally used in resolve if needed
        Plugins can enrich the model
        '''
        import ckanext.jsonschema.view_tools as _vt

        return _vt.get_model(package_id, resource_id)




JSONSCHEMA_IBINDER_PLUGINS = PluginImplementations(IBinder)
JSONSCHEMA_IVIEW_PLUGINS = PluginImplementations(IJsonschemaView)

def get_all_jsonschema_plugins():
    jsonschema_plugins = [] #all jsonschema plugins

    for plugin in JSONSCHEMA_IBINDER_PLUGINS:
        if plugin not in jsonschema_plugins:
            jsonschema_plugins.append(plugin)

    for plugin in JSONSCHEMA_IVIEW_PLUGINS:
        if plugin not in jsonschema_plugins:
            jsonschema_plugins.append(plugin)

    return jsonschema_plugins