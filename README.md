# ckanext-jsonschema

Provides an extensible jsonschema + json based metadata support.

The UI is based on json-editor and can be customized and extented (also via js modules).

The plugin provides a generic packages and resource views in to edit and show.

Provide an iso19139 implementation and a simplified profile and several types already implemented.

Provide several extension points to introduce new dataset and resource formats in other (json based) formats (f.e. STAC).

Importer:
The importer should be ready here:
https://{CKAN_URL}/jsonschema/importer


The url may return an XML iso, you can obtain one going over a geonetowrk metadata page and select donwload (top right) format xml

Example:

here is a metadata url (view)

https://{GEONETWORK_URL}/srv/eng/catalog.search#/metadata/{UUID}

Resulting xml will be (download):

https://{GEONETWORK_URL}/srv/api/records/{UUID}/formatters/xml?approved=true

- destination format should be iso19139
- source format xml.
- organization: choose yours.

Metadata is imported as private or an error is reported.

The final result of the import will be automatically translated into a simplified iso metadata.

Please return json and url used.

Ref:
https://github.com/ckan/ckan/discussions/6364



### Extraction flow

The plugin inherits the interface **IDatasetForm** and overrides the actions *create_package_schema* and *update_package_schema* to validate and convert data coming from users.

It adds 4 methods that are executed in the order in which they are introduced below:

- *schema_check*: this method uses the Draft7Validator to validate the data against the appropriate JSONSchema. If the validation is unsuccessful, the process stops here.

The next 3 methods call methods of the plugin which manages the specific format, so that it can add its custom implementation :

- *before_extractor*: calls the plugin's implementation *before_extractor*. Can be used as preprocessing step

- *extractor*: calls the plugin's implementation of *extract_from_json*. Create the data model from the incoming body, modifying the body in a UI suitable form

- *resource_extractor*: for each item in the field "resources" of the data, calls the method *extract_from_json* passing the specific resource type. Plugins should check the type passed in to choose the right implementation to use

  

### Validation

Dataset and resources are matched against JSON schema files to validate them.

The validations happens both at frontend and backend.



![image-20220121132432873](README-resources/validation.png)



When the edit page is requested, the JSONEditor library fetches the JSONschema files necessary for the specific item that is being edited; it also resolves nested references in the schemas.



The user can use two different editors at frontend, provided by the library JSONschema, with two different validators.

If "HowTo" is selected (which is the default choice), a form is presented to the user. 

The form is automatically constructed using the  JSON schema file corresponding to what is being edited; the same schema is also used for the validation.

![image-20220121132821442](README-resources/howto.png)



If the user switches to the "Editor" mode, then a vanilla editor pops-up, where the JSON can be directly edited.

![image-20220121135211037](README-resources/editor.png)

For both approaches, the validation is executed when the value of any fields changes ("onchange" listener).



If there are validation errors, they are listed at the bottom of the page. Also, the confirm button is disabled, and if the error occured in the "Editor" mode, it is not possible to switch to "HowTo" mode without solving the errors beforehand.

![image-20220121135211037](README-resources/validation_error.png)



When the validation is successfully, it is possible to use the confirmation button. Upon pressing the button, the form is disabled to prevent any change to the data before that the update is completed.

At this point, the request is sent to the backend, and validation also occurs on this side. If there are no errors, the process is completed; otherwise the page is reloaded and the errors are displayed on the top.


### Important Notes

To be able to use insert the "license" field in the json body, this plugin creates the a schema file for license the first time it is needed.
This file is written at PATH_SCHEMA/PATH_CORE_SCHEMA, so the process MUST have permission to write at PATH_SCHEMA, otherwise the startup will file (the creation of subpaths is managed by the code).

From CKAN 2.8.9 it should be possible to create the file at the startup, so the lazy machinery could be avoided.