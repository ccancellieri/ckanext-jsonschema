
import os
import json


def _json_load(folder, name):
    '''
    use with caution: the 'folder'
    param is considered trusted (may never be exposed)
    '''
    try:
        file=os.path.realpath(os.path.join(folder,name))
        # ensure it's a file and is readable
        isfile=os.path.isfile(file)
        # ensure it's a subfolder of the project
        issafe = os.path.commonprefix([file, folder]) == folder
        if isfile and issafe:
            with open(file) as s:
                return json.load(s)
        else:
            return None
    except Exception as ex:
        raise Exception("Schema named: {} not found, please check your schema path folder: {}".format(name,str(ex)))

def _find_all_js(root):
    import os
    _dict={}
    for subdir, dirs, files in os.walk(root):
        for filename in files:
            if filename.endswith('.js'):
                name=os.path.splitext(filename)[0]
                _dict[name]= os.path.join(subdir,filename)
                # with open(os.path.join(subdir,filename), 'r') as f:
                #     _dict[name]= f.readlines()
    return _dict

def _read_all_json(root):
    import os
    _dict={}
    for subdir, dirs, files in os.walk(root):
        for filename in files:
            if filename.endswith('.json'):
                # filename=os.path.realpath(os.path.join(subdir,filename))
                _dict[os.path.splitext(filename)[0]]=_json_load(root,filename)
    return _dict


import xmltodict
import pprint
import json

def xml_to_json_from_file(xml_file, namespaces = None):
    with open(xml_file) as fd:
        return xml_to_json(fd, namespaces = namespaces)

def xml_to_dict(xml_doc, namespaces = None):
    return xmltodict.parse(xml_doc, namespaces = namespaces)


def xml_to_json(xml_doc, namespaces = None):
    # doc = xmltodict.parse(xml_doc, process_namespaces=with_namespace)
    return json.dumps(xml_to_dict(xml_doc, namespaces))

    # pp = pprint.PrettyPrinter(indent=4)
    # return pp.pprint(json.dumps(doc))
    

def json_to_xml(json):
    return xmltodict.unparse(json, pretty=True)