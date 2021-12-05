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