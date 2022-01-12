import os

import requests
import json
import csv
import os
import argparse
from collections import defaultdict


parser = argparse.ArgumentParser(description='Required Arguments')
parser.add_argument('--file', dest='file', type=str,required=True, help='Name of the uuid file in csv format (required)')
parser.add_argument('--key', dest='key', type=str,required=True, help='CKAN Auth key (required)' )
parser.add_argument('--url', dest='url', type=str,required=True, help='CKAN target url (required)')
parser.add_argument('--surl', dest='surl', type=str,required=True, help='geonetwork source url (required)')
parser.add_argument('--pupdate', dest='pupdate', type=str, help='Package Update (optional) by default its false in case of update the already published metadata set it to true')
parser.add_argument('--jtype', dest='jtype', type=str, help='Jsonschema Type (optional) by default iso19139')
parser.add_argument('--fxml', dest='fxml', type=str, help='from Xml (optional) by default its true ')
args = parser.parse_args()
columns = defaultdict(list)
# 1st argrument uuid file
uuid_file=args.file
# 2nd ckan auth key
ckan_auth_key=args.key
# 3rd baseurl of target ckan
ckan_target_url=args.url
# 4th source url of geonetwork
geonetwork_source_url=args.surl
# 5th package update optional argument
ckan_package_update=args.pupdate
# 5th json schema type optional
ckan_json_type=args.jtype
# 6th from xml optional
ckan_from_xml=args.fxml

if ckan_package_update=='true':
    ckan_package_update = True
else:
    ckan_package_update = False

if ckan_json_type:
    ckan_json_type
else:
    ckan_json_type='iso19139'

if ckan_from_xml=='false':
    ckan_from_xml=False
else:
    ckan_from_xml=True

def append_data_tocsv_and_json(uuid,response):
    jsonresponse=response.json()
    if not os.path.isfile('results/result.csv'):
        with open(r'results/result.csv', 'w') as f:
            fields = ['uuid', 'response_status', 'response_content_success']
            writer = csv.DictWriter(f, fields)
            writer.writeheader()
            writer.writerow({"uuid": uuid, "response_status": response.status_code,
                             "response_content_success": jsonresponse.get('success')})
    else:
        with open(r'results/result.csv', 'a', newline='') as f:
            fields = ['uuid', 'response_status', 'response_content_success']
            writer = csv.DictWriter(f, fields)
            writer.writerow({"uuid": uuid, "response_status": response.status_code,
                             "response_content_success": jsonresponse.get('success')})
    if jsonresponse.get('success')==False:
        with open('results/'+uuid+'.json', "w") as out_file:
            json.dump(jsonresponse.get('error'), out_file)

with open(uuid_file) as f:
    reader = csv.DictReader(f) # read rows into a dictionary format
    for row in reader: # read a row as {column1: value1, column2: value2,...}
        for (k,v) in row.items(): # go over each column name and value
            columns[k].append(v)

uuid_list=columns['uuid']
owner_org_ilist=columns['owner_org']
for uuid, owner_org in zip(uuid_list, owner_org_ilist):
    url = ckan_target_url

    session = requests.Session()
    session.headers.update({"accept" : "application/xml"})
    session.headers.update({"Content-Type": "application/json"})
    session.headers.update({'Authorization': ckan_auth_key})

    data ={
      'url': geonetwork_source_url + '/srv/api/records/' + uuid + '/formatters/xml?approved=true',
      'jsonschema_type': ckan_json_type,
      'from_xml': ckan_from_xml,
      'package_update': ckan_package_update,
      'owner_org':owner_org,
      'import':'import'
    }


    final_data=json.dumps(data)
    resp = session.post(url, headers=session.headers, data=final_data)
    print (resp)
    append_data_tocsv_and_json(uuid,resp)





