
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

                key_prefix = ""
                if root != subdir:
                    key_prefix = subdir.replace(root + os.sep, "")

                file_path = os.path.join(key_prefix, filename)
                file_content = open(os.path.join(root, file_path)).read()

                _dict[file_path] = file_content

    return _dict


def _read_all_json(root, prefix=""):
    import os
    _dict={}
    for subdir, dirs, files in os.walk(root):
        for filename in files:
            if filename.endswith('.json'):

                key_prefix = ""
                if root != subdir:
                    key_prefix = subdir.replace(root + os.sep, "")

                key = os.path.join(key_prefix, filename)

                _dict[key]=_json_load(subdir,filename)

    return _dict

def _get_key(filename):  
    return os.path.splitext(filename)[0]


import xmltodict
import pprint
import json

# namespaces = {u'http://www.opengis.net/gml/3.2': u'gml', u'http://www.isotc211.org/2005/srv': u'srv', u'http://www.isotc211.org/2005/gts': u'gts', u'http://www.isotc211.org/2005/gmx': u'gmx', u'http://www.isotc211.org/2005/gmd': u'gmd', u'http://www.isotc211.org/2005/gsr': u'gsr', u'http://www.w3.org/2001/XMLSchema-instance': u'xsi', u'http://www.isotc211.org/2005/gco': u'gco', u'http://www.isotc211.org/2005/gmi': u'gmi', u'http://www.w3.org/1999/xlink': u'xlink'}
# # TODO DEBUG
# import ckanext.jsonschema.utils as _u
# import os
# j = _u.xml_to_json_from_file(os.path.join(_c.PATH_TEMPLATE,'test_iso.xml'))
# import json
# _j=json.loads(j)
# _namespaces=_j['http://www.isotc211.org/2005/gmd:MD_Metadata']['@xmlns']
# namespaces = dict((v,k) for k,v in _namespaces.iteritems())
# _u.json_to_xml()
# _u.xml_to_json_from_file(os.path.join(_c.PATH_TEMPLATE,'test_iso.xml'), True, namespaces)

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

    
def _initialize_license_schema():
    """This will break if there is non custom license group, which is if the licenses_group_url key is unset"""
    
    import ckan.model as model
    import ckanext.jsonschema.constants as _c 


    licenses = model.Package.get_license_options()

    enum_ids = []
    enum_titles = []

    for license in licenses:    
        enum_titles.append(license[0])
        enum_ids.append(license[1])

    data = {
        "enum": enum_ids,
        "options": {
            "enum_titles": enum_titles
        }
    }

    
    path = os.path.join(_c.PATH_SCHEMA, _c.PATH_CORE_SCHEMA)

    if not os.path.exists(path):
        os.makedirs(path)

    file_path = os.path.join(path, "licenses.json")

    with open(file_path, "w") as f:
        f.write(json.dumps(data))

def all_files_in_path_recursive(path, ext):
    import os
    
    all_files = []

    for subdir, dirs, files in os.walk(path):
        for filename in files:
            if filename.endswith(ext):

                # this block gets the relative path starting at <path>
                key_prefix = ""
                if path != subdir:
                    key_prefix = subdir.replace(path + os.sep, "")

                all_files.append(os.path.join(key_prefix, filename))

    return all_files
