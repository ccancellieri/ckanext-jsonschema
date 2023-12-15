# What is ckanext-jsonschema

This plugin provide a quite extensive set of functionalities to introduce **jsonschema based metadata types** into CKAN  (>=2.8) metadata.

It also provide an **User Interface** (UI) based on the [json-editor](https://github.com/json-editor/json-editor) library to properly **edit** and **validate** complex json fields.
The UI can also be customized in terms of components and autocompletion capabilities via javascript modules.

Provide an iso19139 implementation and a simplified profile and several types already implemented.

Provide several extension points to introduce new dataset and resource formats in other (json based) formats (f.e. STAC).


## How it works

Leveraging on the extra fields capabilities of CKAN, the jsonschema plugin is defining three extra predefined and fixed custom fields.

These will be used extensively to add json and jsonschema capabilities to CKAN.

The goal is to simplify the way a metadata mapping is performed in CKAN. 

These fields could be attached to the dataset, resource or view objects of CKAN.

## Basic functionalities :

Registry : 

This functionality drives the behaviours of jsonschema plugin. Each plugin  can define its own registry to define its own types with configurations. In case you need more details please reference the [Registry section in development documentation](README_DEV.md###Registry)

Validator :

This functionality of jsonschema plugin makes it possible to dynamically validate user inputs.In case you need more details please reference the [Validator section in development documentation](README_DEV.md#validator)

View Configurations : 

This functionality allows each plugin to have multiple view types.In case you need more details please reference the [View Configurations section in development documentation](README_DEV.md#view-configurations)

## ADDITIONAL FUNCTIONALITIES

Json addition is just a way to store JSON's in CKAN providing an interface and a validation. On top of these feature jsonschema implements some additional functionalities:

Extractor(from JSON to CKAN or reverse)

Importer:

This functionality can be used to import metadata from an external repository, it can be in any supported format (f.e. from geonetwork).In case you need more details please reference the [Importer section in development documentation](README_DEV.md#importer)

Exporter:

This functionality can be used to export a metadata in CKAN to a standart XML.In case you need more details please reference the  
In case you need more details please reference the [Exporter section in development documentation](README_DEV.md#exporter)

Cloner:

This functionality provides an interface to duplicate an existing metadata.
In case you need more details please reference the [Cloner section in development documentation](README_DEV.md#cloner)

Harvester:?

Resolver:

This functionality allows a change in a CKAN object to be reflected into another object that is configured on it. In case you need more details please reference the [Resolver section in development documentation](README_DEV.md#resolver)

Wrapper:

This functionality allows users to compose views into a big collection. In case you need more details please reference the [Wrapper section in development documentation](README_DEV.md#wrapper)




### Views

From the jsonschema perspective, the view is the representation of the metadata. Each change in the metadata may be reflected into every view configured on it.

For example, changing the title or the description of the metadata, could cause a change in the appearance of the view.

<!-- Question do we need this part ? -->






# Installation and Administration 

The jsonschema plugin comes with several plugins. To add their functionalities, these must be configured in the *ckan.plugins* property. 

The plugin which depend on jsonschema can be of two types; they can implement **metadata** (and resource) functionalities or **view** functionalities.

## Plugins overview

| Plugin                  | Version  | Type     | Functionalities                                              |
| ----------------------- | -------- | -------- | :----------------------------------------------------------- |
| jsonschema              | Released | core     | This is the main plugin. It implements several actions related to jsonschema metadata, blueprints and Jinja helpers. It also implements the custom jsonschema indexing for SOLR. This plugin needs to be configured to use any of the following |
| jsonschema_iso          | Released | metadata | Adds support for the *iso* metadata format and for different custom resources |
| jsonschema_stac         | Alpha    | metadata | Adds support for the *stac* metadata format and for the *stac-asset* resource |
| jsonschema_dataset      | Released | metadata | Needed to integrate the jsonschema functionalities with the dataset metadata. It also adds the *JSON* custom resource |
| jsonschema_frictionless | Alpha    | metadata | Adds support for *Tabular Data* custom resource              |
| harvester_iso19139      | Alpha    | metadata | Harvester for iso19139 from GeoNetwork using CSW. Superseded by the importer |


## Installation 

### SOLR

Add the following entry to the SOLR schema.xml:


```xml
<field name="res_ids" type="string" indexed="true" stored="true" multiValued="true"/>
<field name="res_jsonschemas" type="text" indexed="true" stored="true" multiValued="true"/>
<field name="res_jsonschema_types" type="string" indexed="true" stored="true" multiValued="true"/>
<field name="view_ids" type="string" indexed="true" stored="true" multiValued="true"/>
<field name="view_types" type="string" indexed="true" stored="true" multiValued="true"/>
<field name="view_jsonschema_types" type="string" indexed="true" stored="true" multiValued="true" />
<field name="view_jsonschemas" type="text" indexed="true" stored="true" multiValued="true" />
```

Optionally (will only work with the terriajs plugin)
```xml
<field name="bbox_area" type="float" indexed="true" stored="true" />
<field name="maxx" type="float" indexed="true" stored="true" />
<field name="maxy" type="float" indexed="true" stored="true" />
<field name="minx" type="float" indexed="true" stored="true" />
<field name="miny" type="float" indexed="true" stored="true" />

```


Tomcat9 solr:

Due to relaxedQueryPath limits (https://tomcat.apache.org/tomcat-8.5-doc/config/http.html)
we need to properly setup the connector:
nano /etc/tomcat9/server.xml

Setup the connector as following:

```xml
<Connector port="8983" protocol="HTTP/1.1"
                   connectionTimeout="20000"
               redirectPort="8443" relaxedQueryChars="&quot;&lt;&gt;[\]^`{|}"
/>
```

see also:

    "&quot;&lt;&gt;![\]^`{|}"


## Related plugins

| Plugin                    | Version  | Type     | Functionalities | Ref                                                        |
| ------------------------- | -------- | -------- | :-------------- | ---------------------------------------------------------- |
| terriajs                  | Released | view     |                 | https://bitbucket.org/cioapps/ckanext-terriajs             |
| jsonschema_dashboard      | Released | metadata |                 | https://bitbucket.org/cioapps/ckanext-jsonschema-dashboard |
| jsonschema_dashboard_view | Released | view     |                 | https://bitbucket.org/cioapps/ckanext-jsonschema-dashboard |


# API

### Using CKAN's REST API to Manage Data

This guide will walk you through using CKAN's REST API to perform essential data management tasks such as creating packages, resources, and views.

<!-- QUESTION maybe we can talk about how to get an api key ? -->

### Create a Package

To create a package using CKAN's REST API, you can use the following Python code as a starting point:

```python
import requests

# Define your CKAN API URL and API key
api_url = "https://{CKAN_URL}/api/action/package_create"
api_key = "your-api-key"

# Data for creating a new package
data = {
    "name": "my-new-package",
    "title": "My New Package",
    "author": "Your Name",
    # Add more metadata fields as needed
}

headers = {
    "Authorization": api_key,
    "Content-Type": "application/json",
}

response = requests.post(api_url, json=data, headers=headers)

```

### Create a Resource

```python

# Define your CKAN API URL and API key
api_url = "https://{CKAN_URL}/api/action/resource_create"
api_key = "your-api-key"

# Data for creating a new resource
data = {
    "package_id": "your-package-id",
    "name": "my-new-resource",
    "url": "https://url-to-your-data-resource",
    "format": "CSV",
    # Add more metadata fields as needed
}

headers = {
    "Authorization": api_key,
    "Content-Type": "application/json",
}

response = requests.post(api_url, json=data, headers=headers)

```
### Create a View

```python

# Define your CKAN API URL and API key
api_url = "https://{CKAN_URL}/api/action/resource_view_create"
api_key = "your-api-key"

# Data for creating a new view
data = {
    "resource_id": "your-resource-id",
    "title": "My Data View",
    "view_type": "recline_view",
    # Add more view configuration as needed
}

headers = {
    "Authorization": api_key,
    "Content-Type": "application/json",
}

response = requests.post(api_url, json=data, headers=headers)

```

### View Search

    https://{CKAN_URL}/api/action/jsonschema_view_search?view_type={VIEW_TYPE}

This api will try to return and match all the jsonschema based VIEWS indexed into solr

It will only query for Public metadata
 
#### Request type:
	
GET

#### Mandatory params:
|Param|Type|Note|Example|
|--|--|--|--|
| view_type | String | the plugin name which manage the view. currently only | jsonschema_dashboard_view, terriajs |

#### Acceptable params:
|Param|Type|Note|Example|
|--|--|--|--|
| query | String | Full-text search through all the text fields |  |
| package_desc | String |  |  |
| package_name | String |  |  |
| package_title | String |  |  |
| resource_desc | String |  | "my description" |
| resource_name | String |  |  |
| tags | String or Array | List of dataset tags to search for | (food farm rice) |
| data_format | String | Filter resources by format (wms, csv, json etc.) |  |
| organization_name | String or Array | List of organizations to search for  |  |
| join_condition | String | [OR|AND default is AND] | AND |
| schema_type | String | the schema used for the view body it should match with the schema key of the registry, see below |  |
| page_size | Number | Default is 100. There's an hard limit to 1000 packages (which can generate a huge list of views, several for each package) it can be reduced using this parameter | 99 |
| offset | int | Specifies an offset (by default, 0) into the responses at which Solr should begin displaying content. | 0 |


**Notes:**

When passing multiple values to a parameter, you need to have the following in mind:

- **Organizations:** Each Dataset in CKAN can belong to at most one organization. Because of that, if the user wants to search through multiple organizations, the OR condition should be used:

    organization_name: (org1 OR org2)

    **Single selection:**

    http://{CKAN_URL}/api/action/jsonschema_view_search?package_name=* water *&organization_name=wapor


    **Multiple selection:**

    http://{CKAN_URL}/api/action/jsonschema_view_search?package_name=*%20water%20*&organization_name=(wapor OR wapor-3)
    
    If you pass AND instead of OR in the organization parameter, you won't get any results, since there is no dataset that belongs to two Organizations at the same time
    

- **Tags:** Each Dataset in CKAN can have 0 or many tags. Because of that, if the user wants to search through multiple tags, the OR or AND condition can be used:

    tags: (tag1 AND tag2 OR tag3)

    **Single selection:**

    http://{CKAN_URL}/api/action/jsonschema_view_search?package_name=* water *&tags=wapor

    **Multiple selection:**

    http://{CKAN_URL}/api/action/jsonschema_view_search?package_name=* water *&tags=(wapor OR wapor-3 AND air)

    **NOTE:**  When sending the API request programmatically make sure to add escape characters appropriately

    Example: http://{CKAN_URL}/api/action/jsonschema_view_search?package_name=*%20water%20*&tags=(wapor OR wapor-3 AND air)

- **Searching through both Organizations and Tags:** When passing multiple parameters to the API, it is important to pass the join_condition parameter, if not passed the default one (AND) is going to be used

    **Single selection:**

    http://{CKAN_URL}/api/action/jsonschema_view_search?package_name=* water *&tags=wapor&organization_name=wapor


    **Multiple selection:**

    http://{CKAN_URL}/api/action/jsonschema_view_search?package_name=* water *&tags=(wapor OR wapor-3 AND air)&organization_name=(wapor OR wapor-3)

    **NOTE:**  When sending the API request programmatically make sure to add escape characters appropriately

    Example: http://{CKAN_URL}/api/action/jsonschema_view_search?package_name=*%20water%20*&tags=(wapor OR wapor-3 AND air)


### Response:
|Param|Type|Note|Example|
|--|--|--|--|
| package  | String | Package metadata information: id, name, title, description, license_id/license_title, tags, author, maintainer, creator_user_id |  |
| organization  | String | Organization metadata: id, name, title, description |  |
| package_id  | String | ID of the package |  |
| resource_id  | String | ID of the resource |  |
| view_id  | String | ID of the view |  |
| metadata_link  | String (url) | WEB page url |  |
| packages  | list of dictized datasets | Package metadata information: id, name, title, description, license_id/license_title, tags, author, maintainer, creator_user_id |  |
| package_count  | int | Number of returned packages (datasets), can be page_size or the total number of found datasets if less then 100 |  |
| offset  | int | offset parameter of the API call |  |
| total_package_count  | int | total number of packages (datasets) found in SOLR |  |
| view_count  | int | total number of views in the returned package_count datasets |  |
As mentioned above the packages key, returnes a list of dictized datasets. Each of them contains the following keys:
|Param|Type|Note|Example|
|--|--|--|--|
| id  | String | Unique identifier of the dataset |  |
| name  | String | Name of the dataset - Unique identifier of the dataset |  |
| title  | String | Title of the dataset |  |
| notes  | String | Description of the dataset |  |
| type  | String | Type of the dataset (dataset or iso) |  |
| url  | String (url) | URL pointing to the dataset |  |
| private  | String | visibility of the Dataset (ture/false) |  |
| isopen  | String | Legacy - openness of the dataset according to licence [NOT USED] |  |
| state  | String | State of the resource (active/deleted) |  |
| num_tags  | int | Number of tags per Dataset |  |
| tags  | list of tag dictionaries | The dataset’s tags |  |
| license_title  | String | Title of the License associated with the dataset |  |
| license_id | String | Unique identifier of the License associated with the dataset |  |
| num_resources  | int | Total number of resources per Dataset |  |
| extras  | list of extra dictionaries | The dataset’s extra metadata (not included in the default CKAN metadata model) |  |
| owner_org  | String | unique identifer of the owner organization |  |
| organization  | dictionary| The owner organization metadata |  |
| groups  | list of resources dictionaries | The groups to which the dataset belongs |  |
| num_resources_view  | int | Number of views per Dataset satisfyling the search criteria |  |
| views  | list of resources dictionaries | Resources metadata per view |  |
| maintainer  | String | Maintainer of the Dataset |  |
| maintainer_email  | String | Maintainers email address |  |
| author  | String | Author of the Dataset |  |
| author_email  | String | Author email address |  |
| creator_user_id  | String | Unique identifier of the user that created the dataset |  |
| metadata_created  | Date | Date when the dataset was created |  |
| metadata_modified  | Date | Date when the dataset was last modified |  |
| relationships_as_object  | list of relationship dictionaries | Relationship between two datasets (packages) [NOT USED] |  |
| relationships_as_subject  | list of relationship dictionaries | Relationship between two datasets (packages) [NOT USED] |  |
| revision_id  | list of resources dictionaries | Unique identifier of the dataset |  |
Views key contains a list of dictized resources that satisfy the view_type search criteria. Each of them has the following keys:
|Param|Type|Note|Example|
|--|--|--|--|
| id  | String | Unique identifier of the resource |  |
| package_id  | String | Unique identifier of the dataset |  |
| name  | String | Name of the resource |  |
| size  | int | Size of the resource file |  |
| state  | String | State of the resource (active/deleted) |  |
| description  | String | Description of the resource |  |
| format  | String | Format of the resource |  |
| metadata_link  | String (url) | WEB page url to the dataset |  |
| url  | String (url) | URL pointing to the resource |  |
| resource_link  | String (url) | WEB page url |  |
| jsonschema_body_link | String (url) | REST API |  |
| view_type  | String | may match the **type** parameter | terriajs |
| jsonschema_body | String (Json) | Resolved view body | {"key":"value"} |
| jsonschema_type | String | may match the schema used from the registry, see below | wms |
| jsonschema_opt | String (Json) | meta-metadata optional informations, should never be exposed but can ship some hints |  |


Organization key is a list of key/value pair details for the owner_organization.
|Param|Type|Note|Example|
|--|--|--|--|
| id  | String | Unique identifier of the organization |  |
| name  | String | Name of the organization - Unique identifier of the organization |  |
| title  | String | Title of the organization |  |
| description  | String | Description of the organization |  |

**Notes:**
 - In case of spaces values please quote the string with "value with spaces"
 - In case of full you could try to use star notation but it's not guarantee a full text search (f.e.: "*value with *")


## View List

    https://{CKAN_URL}/api/action/jsonschema_view_list?package_id={VIEW_TYPE}

This api will try to return all the jsonschema based VIEWS indexed into solr from a specific package

It will only query for Public metadata
 
### Request type:
	
GET

### Mandatory params:
|Param|Type|Note|Example|
|--|--|--|--|
| package_id  | String | The ID or the Name of the package |  |

### Response:
|Param|Type|Note|Example|
|--|--|--|--|
| package_id  | String | ID of the package |  |
| resource_id  | String | ID of the resource |  |
| view_id  | String | ID of the view |  |
| metadata_link  | String (url) | WEB page url |  |
| resource_link  | String (url) | WEB page url |  |
| jsonschema_body_link | String (url) | REST API |  |
| view_type  | String | may match the **type** parameter | terriajs |
| jsonschema_body | String (Json) | Resolved view body | {"key":"value"} |
| jsonschema_type | String | may match the schema used from the registry, see below | wms |
| jsonschema_opt | String (Json) | meta-metadata optional informations, should never be exposed but can ship some hints |  |

**Notes:**
 - In case of spaces values please quote the string with "value with spaces"
 - In case of full you could try to use star notation but it's not guarantee a full text search (f.e.: "*value with *")


### Geospatial search:

Yes we have also bbox indices fetched directly from wms services... (provided by terriajs view plugin) but we are still not able to use the BBOX parameters which are in solr.
TODO we planned to change the solr bbox index leveraging on solr > 4.x



## Body, Type, Opt

These are GET and sideffect free calls which can be used to inspect the content of the fields controlled by the 

    https://{CKAN_URL}/jsonschema/{body|type|opt}/{PACKAGE_ID}[/{RESOURCE_ID}[/{VIEW_ID}]]

## Clone (webpage)

    https://{CKAN_URL}/jsonschema/clone

## Importer (webpage)

    https://{CKAN_URL}/jsonschema/importer

## Validate (webpage)

    https://{CKAN_URL}/jsonschema/validate


## Registry

Returns all the available (registered) jsonschema types

    https://{CKAN_URL}/jsonschema/registry[/jsonschema_type]
 
### Request type:
	
GET

## Schema, template and javascript modules

For each registry entry you may want to retrieve the **schema**, the **template** or the **javascript modules**

    https://{CKAN_URL}/jsonschema/{schema|template|module}/jsonschema_type_path.{json|js}

The javascript **module** is loaded into the interface and can be used to provide autocompletion for a specific jsonschema_type and for several othe extensions point (ref to the json-editor library for a list)

The **template** is used to populate an empty type when it is created

The **schema** is the jsonschema definition of the associated type


### Request type:
	
GET



## View specific params

When you have a view based on the jsonschema plugin you may (it depends on the specific implementation) have some additional arguments
available:

https://{CKAN_URL}/jsonschema/{body|type|opt}/{PACKAGE_ID}/{RESOURCE_ID}/{VIEW_ID}

To understand the following optional parameter we may describe the concept of item and the resolution:

### wrap

wrap=true is a simple way to ask to the implementing plugin to return a **config** (potentially dynamically generated) starting from an **item**. In case you need more details please reference the [Additional Functionalities section](#additional-functionalities)


So if your view is defining an **item** and the url is the following:

    https://{CKAN_URL}/jsonschema/body/{PACKAGE_ID}/{RESOURCE_ID}/{VIEW_ID_OF_THE_ITEM}

To obtain a config to pass to your application viewer you may pass:

    https://{CKAN_URL}/jsonschema/body/{PACKAGE_ID}/{RESOURCE_ID}/{VIEW_ID_OF_THE_ITEM}?wrap=true

Which may wrap the view (body) of the **item** you are referring to into a fake or dynamically generated **config** that your application will recognize as valid.

Obviously all of the above is totally optional if the implementing plugin and the viewer do not need to group items.

This is instead largely used by the terriajs and the Dashboard plugins.

### resolve

resolve=true is a way to ask a change in a CKAN object to be reflected into another object that is configured on it. In case you need more details please reference the [Additional Functionalities section](#additional-functionalities)

For example if a view jsonschema_body contains:

```json
{
    "name":"{{resource.name}}",
    "description": "{{package.notes or resource.description}}"
}
```

Using the resolve=true parameter the expected returned body will be:

https://{CKAN_URL}/jsonschema/body/{PACKAGE_ID}/{RESOURCE_ID}/{VIEW_ID_OF_THE_ITEM}?resolve=true


```json
{
    "name":"The name of the resource",
    "description": "The description of the package (or the one from the resource)"
}
```
<!-- QUESTION otherwise the values will not be reloaded and old values will be returned right ? if so this may also be added here-->

### force_resolve

To enforce the resolution of an already resolved view, use this parameter.

### Acceptable params:
|Param|Type|Note|Example|
|--|--|--|--|
| wrap | Boolean | Is used to provide a default wrapping structure when the item is not the first  | resolve=False |
| resolve | Boolean |  | resolve=True |
| force_resolve | Boolean |  | force_resolve=True |



<!-- Question i feel like the next section should also be here -->
# Provided plugins:

## jsonschema

base plugin to enable extensions points provide basic jsonschema functionnalities

## jsonschema_iso19139

extension to provide an iso19139 binding from iso19139 and the below simplified iso profile

## jsonschema_iso

extension to provide a simplified but quite complet iso model

## harvester_iso19139 (deprecated, ise importer)

An harvester from CSW to iso19139/iso

requires harves plugin to be installed, also has a dedicate requirements file

## Suggested configuration:

    jsonschema jsonschema_iso19139 jsonschema_iso

know issue:
---
 the xml importer is encountering some runtime issue (due to xml format body) with the google analytics extension.