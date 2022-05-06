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



### How it works

Leveraging on the extra fields capabilities of CKAN, we are defining these 3 custom extra fields.

These will be used extensively for the definition of the content and behaviours of the types implemented by the jsonschema plugins 

These fields will be attached to the default domain objects of CKAN (datasets, resources and views) 

<!--TODO: Groups, Organizations-->

<!--TODO: show buttons under metadata/resources-->

Then main usage of this additions is to use json and json-schema to define models of domain objects which vary in complexity, on which the logic of each plugins works.

The body of jsonschema objects is commonly used as **single source of truth**, generating an **extraction** **flow** from the json to CKAN fields. 

This is quite useful and easy to implement when you need predefined indexing and mapping logic for any type of JSON.    

The jsonschema_iso plugin extensively use this approach.



### # TODO Describe jsonschema_type, jsonschema_body, jsonschema_opt (meta-metadata)

The **jsonschema_type** is a string field which identifies a specific jsonschema type. The type is then used widely in the plugin to referr to its configuration (see below: Registry    )



### Views

From the jsonschema prospective, the view is the representation of the metadata. Each change in the metadata may be reflected into every view configured on it.

For example, changing the title or the description of the metadata, could cause a change in the appearance of the view.

For this reason we introduce for all the jsonschema views the concepts of Resolution and Wrapping, which utility is explained in the following paragraphs.

The terriajs plugin extensively use this approach.

Also, jsonschema introduces indexing for view: this is very useful to search views when creating complex and interconnected views.

**Resolution **(copy something from terria)

**Wrapping** 





### A deeper look

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





###  

### Installation 

The jsonschema plugin comes with several plugins. To add their functionalities these must configured in the *ckan.plugins* property. 

The plugin which depend on jsonschema can be of two types; they can implement **metadata** (and resource) functionalities or **view** functionalities.

| Plugin                  | Version  | Type     | Functionalities                                              |
| ----------------------- | -------- | -------- | :----------------------------------------------------------- |
| jsonschema              | Released | core     | This is the main plugin. It implements several actions related to jsonschema metadata, blueprints and Jinja helpers. It also implements the custom jsonschema indexing for SOLR. This plugin needs to be configured to use any of the following |
| jsonschema_iso          | Released | metadata | Adds support for the *iso* metadata format and for different custom resources |
| jsonschema_stac         | Alpha    | metadata | Adds support for the *stac* metadata format and for the *stac-asset* resource |
| jsonschema_dataset      | Released | metadata | Needed to integrate the jsonschema functionalities with the dataset metadata. It also adds the *JSON* custom resource |
| jsonschema_frictionless | Alpha    | metadata | Adds support for *Tabular Data* custom resource              |
| harvester_iso19139      | Alpha    | metadata | Harvester for iso19139 from GeoNetwork using CSW. Superseded by the importer |



**Related plugins** 

| Plugin                    | Version  | Type     | Functionalities | Ref                  |
| ------------------------- | -------- | -------- | :-------------- | -------------------- |
| terriajs                  | Released | view     |                 | ...                  |
| jsonschema_dashboard      | Released | metadata |                 | (Private repository) |
| jsonschema_dashboard_view | Released | view     |                 | (Private repository) |



### Configuration

#### Schemas, Templates, Modules

Each type of jsonschema entity can have a corresponding:

- **schema**: which defines the schema of the object, using the json-schema framework (https://json-schema.org/)
- **template**: a json object which respects the json-schema definition and is used when a new instance is being created as a default value
- **module**: a javascript file which includes additional functionalities for the editor

The jsonschema plugin ships with schema, template and modules for the types that it implements. 

When CKAN starts, jsonschema reads these files and creates a in-memory catalog where they are stored.



Plugins that implement additional types should register their schemas, templates and modules into the jsonschema catalog (using the interfaces methods).

The default mechanism to do so is to store these resources under *<plugin_source_folder>/**setup**/**schema**/<plugin_name>*,

*<plugin_source_folder>/**setup**/**template**/<plugin_name>*, *<plugin_source_folder>/**setup**/**module**/<plugin_name>*, and then merge them into the catalog.

(Ref to functions *add_schemas_to_catalog, add_templates_to_catalog, add_modules_to_catalog* in tools.py)

 

#### Registry 

The jsonschema plugin behaviours are driven by its **registry**.

Each plugin defining new types, may update the jsonschema's registry.

Each plugin  implementation can define its own registry.json to define its own types. 

(Ref to *add_to_registry* in tools.py)



The **registry.json** consists of a json whose entry are widely used into the jsonschema implementation.

For each entry:

- the key is the **jsonschema_type** which that configuration refers to (it can be referred to a **metadata**, **resource** or **view** type)
- the value is the configuration related to that type



An example entry is showed below:

```json
"iso": {

​    "label": "Iso",

​    "plugin_name": "jsonschema_iso",

​    "schema": "iso/iso.json",

​    "template": "iso/iso.json",

​    "module": "iso/iso.js",

​    "supported_jsonschema_fields": ["body", "opt"],

​    "supported_ckan_fields": ["license_id", "owner_org"]

}
```



Most of the configurations are in common between metadatas, resources and views; some are reserved for views.

Below is a comprehensive list of possible values:

| Property Name                   | Entity | Type             | Usage                                                        |
| ------------------------------- | :----- | ---------------- | ------------------------------------------------------------ |
| label                           | common | String           | The label for the jsonschema_type. This is used in the CKAN UI's (for example, for resources it is the label shown in the dropdown) |
| plugin_name                     | common | String           | This is the name of the plugin that implements the entity. The plugin will be used when manipulating entities of this type |
| schema                          | common | String           | Path to the jsonschema for the type, relative to the main path of schemas |
| template                        | common | String           | Path to the template for the type, relative to the main path of templates |
| module                          | common | String           | Path to the module for the type, relative to the main path of modules |
| supported_jsonschema_fields     | common | Array of Strings | List of jsonschema fields to display in the UI for that type. Possible values are: *body*, *opt* |
| supported_all_jsonschema_fields | common | Boolean          | If true, enables all jsonschema fields in the UI (overrides supported_jsonschema_fields) |
| supported_ckan_fields           | common | Array of Strings | List of default CKAN's fields to display in the UI for that type. Possible values are: <br />- for metadata: *title, url, custom, notes, tags, license_id, owner_org, author, maintainer, version* <br />- for resources: *name, description, format, url, metadata_fields*<br />- for views: *title, description, filters* |
| supported_all_ckan_fields       | common | Boolean          | If true, enables all default CKAN's fields in the UI  (overrides supported_ckan_fields) |
| skip_indexing                   | common | Boolean          | If true, the jsonschema fields of that metadata, resource or view will not be indexed into SOLR |



### Configuration

##TODO Table for variables (PATHS)

##TODO Folder structure

##DO NOT INSERT "core" folder



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

<field name="res_ids" type="string" indexed="true" stored="true" multiValued="true"/>
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