import ckan.authz as authz
from ckan.common import _
from ckan.logic import side_effect_free

# GET ACTION
# http://localhost:5000/api/action/jsonschema_reload
@side_effect_free
def reload(context, data_dict):
    import ckanext.jsonschema.tools as _t

    if not authz.is_sysadmin(context[u"user"]):
        return {'success': False, 'msg': _('Only sysadmin can perform this action')}

    try:
        _t.reload()
        return { "success": True }    
    except Exception as e:
        return { "success": False, "msg": str(e)}
