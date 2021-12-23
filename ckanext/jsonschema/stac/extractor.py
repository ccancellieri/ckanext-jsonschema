import uuid, ckan.lib.helpers as h, ckan.lib.munge as munge, ckanext.jsonschema.validators as _v
from ckanext.jsonschema.stac import constants as _c

def _extract_id(dataset_type, body):
    if dataset_type == _c.TYPE_STAC:
        return body.get('id')


def _extract_json_name(body, type, opt, version, data, errors, context):
    
    name = _extract_id(type, body)
    
    if not name:
        name = str(uuid.uuid4())
    else:
        name = munge.munge_name(name)

    body['id'] = name
    
    _dict = {
        'name': name, 
        'url': h.url_for(controller='package', action='read', id=name, _external=True)
       }
    data.update(_dict)


def _extract_from_json(body, type, opt, version, data, errors, context):
    
    try:
        _extract_json_name(body, type, opt, version, data, errors, context)
    except Exception as e:
        _v.stop_with_error(('Error decoding metadata identification: {}').format(str(e)), 'metadata identifier', errors)

    return (body, type, opt, version, data)