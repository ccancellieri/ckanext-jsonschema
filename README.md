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





### Configuration

##TODO Table for variables (PATHS)

##TODO Folder structure

##DO NOT INSERT "core" folder



The operations that can be performed for each package type and resource type implemented by Jsonschema based plugins are configured using JSON files.

This plugin currently supports 4 operations on packages:

- **input**: import packages from an external url
- **supported**: manage the package (create, update, delete...)
- **clone**: create a clone of the package into the CKAN instance
- **output**: export the package in different formats (JSON, XML...)

The operations on resources are:

- **supported**: manage the resource (create, update, delete...)
- **clone**: clone the resource



For each Jsonschema plugin implementing the IBinder interface, you may put a configuration file under the folder **ckanext.jsonschema.path.config** (default is *config/*) called <*plugin_name>.json*.



##### Configuration File

A configuration file has this shape:

`
{
    "plugin_name": "jsonschema_iso",
    "description": "",
    "jsonschema_types": {
        "iso": {
            "package_type": "iso",
            "input": true,
            "supported": true,
            "clone": true,
            "output": true,
            "resources": {
                "tabular-data-resource": {
                    "label": "Table Data Resource",
                    "clone": false,
                    "supported": true
                }
            ...
            }
        },
        ...
    }
}
`



| Property Name    | Path                                                         | Values  | Meaning                                                      |
| ---------------- | :----------------------------------------------------------- | ------- | ------------------------------------------------------------ |
| plugin_name      | root                                                         | String  | The name of the plugin. This is redundant with the configuration filename. |
| description      | root                                                         | String  | Description for the plugin                                   |
| jsonschema_types | root                                                         | Objects | This object contains an object for each jsonschema_type to configure |
| package_type     | jsonschema_types/<jsonschema_type>                           | String  | The name of the package type which this jsonschema_type refers to. The package type is the type saved into the CKAN database. Different jsonschema types can refere to the same package_type |
| input            | jsonschema_types/<jsonschema_type>                           | Boolean | Tells if the input operation is supported for this jsonschema_type. If True, adds the type to the importer interface. |
| supported        | jsonschema_types/<jsonschema_type>                           | Boolean | Tells if the jsonschema_type is supported (should be true for every configured type) |
| clone            | jsonschema_types/<jsonschema_type>                           | Boolean | Tells if the clone operation is supported for this jsonschema_type. |
| output           | jsonschema_types/<jsonschema_type>                           | Boolean | Tells if the clone operation is supported for this jsonschema_type. |
| resources        | jsonschema_types/<jsonschema_type>                           | Object  | This object contains an object for each resource compatible with the jsonschema_type |
| clone            | jsonschema_types/<jsonschema_type><br />/resources/<resource_type> | Boolean | Tells if the clone operation is supported for this resource type under the specific jsonschema_type. If False, the resource will be skipped during a clone operation. |
| suppor           | jsonschema_types/<jsonschema_type><br />/resources/<resource_type> | Boolean | Tells if the resource_type is supported (should be true for every configured type) |

For an example, look at *config/jsonschema_iso.json*

##TODO SCHEMA/TEMPLATE/ LOADING



### Lazy Schema Setup

##TODO Describe the lazy mechanism to 

### License

The Jsonschema plugin overtakes the license field for packages supported by plugins that use Jsonschema.
CKAN's default license field is hidden, and it has to be included into the schema of the package.
To be able to validate the license entry against the list of licenses loaded by CKAN, the list of licenses is materialized as a JSON so that it can be referenced in schemas.

This is done lazily when the file is needed for the first time. 
The file is written at PATH_SCHEMA/PATH_CORE_SCHEMA (default is schema/core/), so the process MUST have permission to write at PATH_SCHEMA, otherwise the startup will file (the creation of subpaths is managed by the code).

##### Schema example

`
"license_id": {
​   "propertyOrder": 1,
​   "title": "License",
​   "type": "string",
​   "$ref": "core/licenses.json"
}`

##### Note

From CKAN 2.8.9 it should be possible to create the file at the startup, so the lazy machinery could be avoided.



## API

## SOLR

Add the following entry to the SOLR schema.xml:


```

<field name="package_id" type="string" indexed="true" stored="true" multiValued="false"/>
<field name="res_ids" type="string" indexed="true" stored="true" multiValued="true"/>
<field name="res_descriptions" type="text" indexed="true" stored="true" multiValued="true"/>
<field name="res_jsonschemas" type="text" indexed="true" stored="true" multiValued="true"/>
<field name="res_jsonschema_types" type="string" indexed="true" stored="true" multiValued="true"/>
<field name="view_ids" type="string" indexed="true" stored="true" multiValued="true"/>
<field name="view_types" type="string" indexed="true" stored="true" multiValued="true"/>
<field name="view_jsonschema_types" type="string" indexed="true" stored="true" multiValued="true" />
<field name="view_jsonschemas" type="text" indexed="true" stored="true" multiValued="true" />


<field name="bbox_area" type="float" indexed="true" stored="true" />
<field name="maxx" type="float" indexed="true" stored="true" />
<field name="maxy" type="float" indexed="true" stored="true" />
<field name="minx" type="float" indexed="true" stored="true" />
<field name="miny" type="float" indexed="true" stored="true" />

```


Tomcat9 sorl:

Due to relaxedQueryPath limits (https://tomcat.apache.org/tomcat-8.5-doc/config/http.html)
we need to properly setup the connector:
nano /etc/tomcat9/server.xml

Setup the connector as following:

```
<Connector port="8983" protocol="HTTP/1.1"
                   connectionTimeout="20000"
               redirectPort="8443" relaxedQueryChars="&quot;&lt;&gt;[\]^`{|}"
/>
```


see also:

"&quot;&lt;&gt;![\]^`{|}"