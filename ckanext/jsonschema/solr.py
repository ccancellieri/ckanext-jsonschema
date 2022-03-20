
# use
# &wt=json for json response writer
# or
# &wt=python
# see https://solr.apache.org/guide/6_6/response-writers.html

def core_exists(core_name):
    # TODO 
    # http://localhost:8983/solr/admin/cores?wt=json&action=STATUS&core=jsonschema_views
    # http://localhost:8983/solr/jsonschema_views/schema?wt=json
    #
    # see also https://solr.apache.org/guide/6_6/coreadmin-api.html#CoreAdminAPI-REQUESTSTATUS

    return False

def core_create(core_name):
    # http://localhost:8983/solr/admin/cores?action=CREATE&name={core_name}
    # #&instanceDir={core_name}
    pass

def core_reindex(jsonschema_type):
    pass

def core_reindex_all():
    # for _type in register.types:
    #     reindex(_type)
    pass

def update(core_name, dict):
    # TODO dict must be flat (defined by an interface method (By jsonschema_type))
    pass

    def configure_fields(core_name, jsonschema_type):
        pass

        # To add a new field to the schema, follow this example from the Bash prompt:

        # $ curl -X POST -H 'Content-type:application/json' --data-binary '{
        # "add-field":{
        #     "name":"new_example_field",
        #     "type":"text_general",
        #     "stored":true }
        # }' https://..../api/collections/jsonschema_views/schema

        # {
        # "add-field":[
        #     { "name":"shelf",
        #     "type":"myNewTxtField",
        #     "stored":true },
        #     { "name":"location",
        #     "type":"myNewTxtField",
        #     "stored":true }]
        # }