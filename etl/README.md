### **JsonSchema ETL**

The JsonSchema ETL allows to perform batch imports into ckan from geonetwork using the JsonSchema plugin.

The ETL:
- Reads the csv file that contains the list of metadata to import in the format *uuid;owner_org*

  For each metadata: 

  - Constructs the appropriate HTTP POST request
  - Makes the request to the specified CKAN instance



##### Script arguments:

| Argument Name | Help                                   | Required | Default  |
| ------------- | -------------------------------------- | -------- | -------- |
| **file**      | Name of the uuid file in csv format    | ✔        |          |
| **key**       | CKAN Auth key                          | ✔        |          |
| **url**       | CKAN target url                        | ✔        |          |
| **surl**      | geonetwork source url                  | ✔        |          |
| **pupdate**   | Package Update (instead of new import) | ❌        | False    |
| **jtype**     | Jsonschema Type                        | ❌        | iso19139 |
| **fxml**      | From Xml                               | ❌        | True     |

 

##### Usage example:

python importer.py  --file "import.csv" --key "ckan-auth-key" --url "url" --surl "surl"
