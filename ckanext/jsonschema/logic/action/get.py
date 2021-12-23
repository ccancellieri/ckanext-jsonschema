import ckan.authz as authz
from ckan.common import _

# GET ACTION
# http://localhost:5000/api/action/jsonschema_reload
def reload(context, data_dict):
    import ckanext.jsonschema.tools as _t

    if not authz.is_sysadmin(context[u"user"]):
        return {'success': False, 'msg': _('Only sysadmin can perform this action')}


    _t.reload()

    return { "success": True }