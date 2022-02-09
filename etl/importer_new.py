import os

import requests
import json
import csv
import os
import argparse
import time
from collections import defaultdict


# Setup parser
parser = argparse.ArgumentParser(description='Required Arguments')
parser.add_argument('--file', dest='file', type=str,required=True, help='Name of the uuid file in csv format (required)')
parser.add_argument('--key', dest='key', type=str,required=True, help='CKAN Auth key (required)' )
parser.add_argument('--url', dest='url', type=str,required=True, help='CKAN target url (required)')
parser.add_argument('--surl', dest='surl', type=str,required=True, help='geonetwork source url (required)')
parser.add_argument('--pupdate', dest='pupdate', type=str, help='Package Update (optional) by default its false in case of update the already published metadata set it to true')
parser.add_argument('--jtype', dest='jtype', type=str, help='Jsonschema Type (optional) by default iso19139')
parser.add_argument('--fxml', dest='fxml', type=str, help='from Xml (optional) by default its true ')
args = parser.parse_args()

# Retrieve arguments and set defaults
# Mandatory
uuid_file = args.file
ckan_auth_key = args.key
ckan_target_url = args.url
geonetwork_source_url = args.surl

# Optionals
ckan_json_type = args.jtype or 'iso19139'
ckan_from_xml = False if args.fxml == 'false' else True
ckan_package_update = True if args.pupdate == 'true' else False



############ FUNCTIONS ############

def do_imports():
    
    uuid_list=columns['uuid']
    owner_org_ilist=columns['owner_org']
    
    for uuid, owner_org in zip(uuid_list, owner_org_ilist):

        try:    
            response = do_import(uuid, owner_org)
            append_data_tocsv_and_json(uuid, response)
            time.sleep(1)
        except Exception as e:
            print(f'Exception importing {uuid}: {repr(e)}')
            raise e


def do_import(uuid, owner_org):
    

    headers = {
        "accept" : "application/xml",
        "Content-Type": "application/json",
        'Authorization': ckan_auth_key
    }

    session = requests.Session()
    session.headers.update(headers)

    data = json.dumps({ 
      'url': geonetwork_source_url + '/srv/api/records/' + uuid + '/formatters/xml?approved=true',
      'jsonschema_type': ckan_json_type,
      'from_xml': ckan_from_xml,
      'package_update': ckan_package_update,
      'owner_org':owner_org,
      'import':'import',
      'license_id': 'CC-BY-NC-SA-3.0-IGO'
    })

    response = session.post(ckan_target_url, data, headers=session.headers)
    print (response)
    
    return response
    

def append_data_tocsv_and_json(uuid,response):
    
    # If output directory doesn't exist, create it
    RESULTS_FOLDER = 'results'
    if not os.path.exists(RESULTS_FOLDER):
        os.mkdir(RESULTS_FOLDER)
    
    RESULTS_PATH = f'{RESULTS_FOLDER}/result.csv'

    # Check if the file already exists, as it is useful
    is_new_file = not os.path.isfile(RESULTS_PATH)
    mode = 'w' if is_new_file else 'a'


    json_response = response.json()
    success = json_response.get('success')
    status_code = response.status_code
    
    with open(RESULTS_PATH, mode, newline='') as f:
        fields = ['uuid', 'response_status', 'response_content_success']
        writer = csv.DictWriter(f, fields)
        
        if is_new_file:
            writer.writeheader()
        writer.writerow({"uuid": uuid, "response_status": status_code, "response_content_success": success})

    # If failed, write a json file with the UUID as name and the error as content 
    if success:
        print(f"Successfully imported {uuid}") 
    else:
        error = json_response.get('error')
        
        with open('results/'+ uuid +'.json', "w") as out_file:
            json.dump(error, out_file)

        print(f"Error importing {uuid}") 


####################################

# EXECUTION
    
columns = defaultdict(list)

with open(uuid_file) as f:
    reader = csv.DictReader(f) # read rows into a dictionary format
    for row in reader: # read a row as {column1: value1, column2: value2,...}
        for (k,v) in row.items(): # go over each column name and value
            columns[k].append(v)

do_imports()



