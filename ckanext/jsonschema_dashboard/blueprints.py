# all gets (schema, template...) for view
# url for in view_template with this url
import json

import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.logic.get as _g
import ckanext.jsonschema.tools as _t
from ckanext.jsonschema.blueprints import jsonschema
from flask import Response, stream_with_context


# create path
def get_view_body(package_id, resource_id, view_id):
    
    view = _g.get_view(view_id)

    return Response(stream_with_context(json.dumps(_t.get_view_body(view))), mimetype='application/json')

jsonschema.add_url_rule('/{}/body/<package_id>/<resource_id>/<view_id>'.format(_c.TYPE,), view_func=get_view_body, methods=[u'GET'])


def get_view_type(package_id, resource_id, view_id):
 
    view = _g.get_view(view_id)

    return Response(stream_with_context(json.dumps(_t.get_view_type(view))), mimetype='application/json')

jsonschema.add_url_rule('/{}/type/<package_id>/<resource_id>/<view_id>'.format(_c.TYPE), view_func=get_view_type, methods=[u'GET'])


def get_view_opt(package_id, resource_id, view_id):

    view = _g.get_view(view_id)

    return Response(stream_with_context(json.dumps(_t.get_view_opt(view))), mimetype='application/json')

jsonschema.add_url_rule('/{}/opt/<package_id>/<resource_id>/<view_id>'.format(_c.TYPE), view_func=get_view_opt, methods=[u'GET'])
