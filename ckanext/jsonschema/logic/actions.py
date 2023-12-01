import json
from datetime import date, datetime

import ckan.lib.navl.dictization_functions as df
import ckan.plugins.toolkit as toolkit
import ckanext.jsonschema.configuration as configuration
import ckanext.jsonschema.constants as _c
import ckanext.jsonschema.indexer as indexer
# import ckanext.jsonschema.logic.get as _g
import ckanext.jsonschema.tools as _t
import ckanext.jsonschema.utils as _u
# import ckanext.jsonschema.validators as _v
from ckan.logic import NotFound, ValidationError, side_effect_free
from ckan.plugins.core import PluginNotFoundException
import ckan.lib.plugins as lib_plugins
import ckan.authz as authz
import ckan.lib.search.query as ckan_query

_ = toolkit._
h = toolkit.h

import logging

log = logging.getLogger(__name__)

import ckan.logic as logic

_check_access = logic.check_access

#@plugins.toolkit.chained_action
def importer(context, data_dict):
    if not data_dict:
        error_msg = 'No dict provided'
        h.flash_error(error_msg,allow_html=True)
        return

    url = data_dict.get('url')
    if not url:
        h.flash_error(_('No url provided'), allow_html=True)
        return

    license_id = data_dict.get('license_id')
    if not license_id:
        h.flash_error(_('License is mandatory'), allow_html=True)
        return


    _check_access('package_create', context, data_dict)
    
    try:
        import requests
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            raise Exception('Unable to fetch data, response status is {}'.format(response.status_code))
    except Exception as e:
        message = str(e)
        log.error(message)
        # e.error_summary = json.dumps(message)
        raise ValidationError(message)

    # body is supposed to be json, if true a  1:1 conversion is provided
    from_xml = data_dict.get('from_xml', 'false').lower() == "true"
    #from_xml = asbool(data_dict.get('from_xml', False))
    try:
        if from_xml:
            body = _u.xml_to_json(response.text)
        else:
            body = response.json() #TODO as json check 
    except Exception as e:
        message = str(e)
        log.error(message)
        # e.error_summary = json.dumps(message)
        raise ValidationError(message)



    # CREATE EXTRAS
    _type = data_dict.get(_c.SCHEMA_TYPE_KEY)
    
    opt = dict(_c.SCHEMA_OPT)
    opt.update({
        'imported' : True,
        'source_format':'xml' if from_xml else 'json',
        'source_url': url,
        'imported_on': str(datetime.now())
    })


    # IMPORT - PREPROCESSING -
    import_context = {}

    package_dict = {
        # IMPORTER_TYPE = 'iso19139'old
        'type': _type,
        'owner_org': data_dict.get('owner_org'),
        'license_id': data_dict.get('license_id'),
        _c.SCHEMA_BODY_KEY: _t.as_dict(body),
        _c.SCHEMA_TYPE_KEY : _type,
        _c.SCHEMA_OPT_KEY : opt,
    }

    errors = []

    try:
        plugin = configuration.get_plugin(_type)
    except PluginNotFoundException as e:
        return { "success": False, "msg": str(e)}

    extractor = plugin.get_input_extractor(_type, package_dict, import_context) 
    extractor(package_dict, errors, import_context)   
    # TODO ######################
    opt['validation'] = False  
    #_t.update_extras_from_context(package_dict, import_context)


    #TODO resources store back to the package_dict
    try:
        # # TODO has deep impact/implications over resources
        is_package_update = data_dict.get('package_update', 'false').lower() == "true"
        #is_package_update = asbool(data_dict.get('package_update', False))
        if is_package_update:
            # errors=[]
            # for plugin in _v.JSONSCHEMA_PLUGINS:
            #     if _type in plugin.supported_dataset_types(opt, _c.SCHEMA_VERSION):
            #         # _body = json.loads(body)
            #         _body = body
            #         id = plugin.extract_id(_body, _type, opt, _c.SCHEMA_VERSION, errors, context)
            #         if id:
            #             pkg = Package.get(id)
            #             if pkg and pkg.type == _type:
            #                 context["package"] = pkg
            #                 _dict={}
            #                 _dict["id"] = pkg.id
            #                 # _dict['type'] = pkg.type
            #                 _dict['extras'] = extras
            #                 return toolkit.get_action('package_update')(context, _dict)
            raise Exception('no support provided for this operation/format')
        else:
            return toolkit.get_action('package_create')(context, package_dict)
    except Exception as e:
        message = str(e)
        log.error(message)
        # e.error_summary = json.dumps(message)
        raise ValidationError(message)
    
    # next_action(context,data_dict)    

def validate_metadata(context, data_dict):

    id = data_dict.get('id')

    # TODO check permissions: package_show?

    package = _t.get(id)

    if package is None:
        raise NotFound("No package found with the specified uuid")

    body = _t.get_package_body(package)
    
    # We need the jsonschema type, so we cannot use _t.get_package_type which would also return datasets
    # _type = _t.get_package_type(package)
    _type = _t._extract_from_package(package, _c.SCHEMA_TYPE_KEY)

    if not _type:
        raise ValidationError("The jsonschema validation is only available on jsonschema metadata")

    errors = {}
    is_error = _t.draft_validation(_type, body, errors)
    
    if is_error:
        raise ValidationError(df.unflatten(errors))


def clone_metadata(context, data_dict):

    source_pkg = _t.get(data_dict.get('id'))
    _type = _t.get_package_type(source_pkg)

    try:
        plugin = configuration.get_plugin(_type)
    except PluginNotFoundException as e:
        return { "success": False, "msg": str(e)}


    package_dict = {
        'resources': [],
        'type': _type,
        'owner_org': data_dict.get('owner_org')
    }
    
    _check_access('package_create', context, package_dict)

    context.update({
        'prevent_notify': True
    })
    clone_context = {}
    # clone_context = {
    #     'prevent_notify': True
    # }

    errors = []

    try:

        cloner = plugin.get_package_cloner(_type)

        if not cloner:
            message = 'No cloner configured for package type {}. Skipping'.format(_type)
            log.info(message)
            return { "success": False, "msg": message}

        cloner(source_pkg, package_dict, errors, clone_context)

        # defaults
        package_dict['private'] = True
        package_dict['title'] = 'Cloned {} {}'.format(source_pkg.get('title',''), datetime.now().isoformat())

        new_pkg_dict = toolkit.get_action('package_create')(context, package_dict)

        for _resource in source_pkg.get('resources'):

            resource = dict(_resource)

            try:
                del resource['id']
                del resource['package_id']

                if 'revision_id' in resource:
                    del resource['revision_id']

                resource['package_id'] = new_pkg_dict['id']
                
                resource_clone_context = {}
                resource_type = _t.get_resource_type(resource)
                
                # default to dataset resource
                if not resource_type:
                    import ckanext.jsonschema.dataset.constants as _dataset_constants
                    resource_type = _dataset_constants.TYPE_DATASET_RESOURCE

                plugin = configuration.get_plugin(_type, resource_type)
                cloner = plugin.get_resource_cloner(_type, resource_type)

                if not cloner:
                    log.info('No cloner configured for resource type {} on package type {}. Skipping'.format(resource_type, _type))
                    continue
                
                resource = cloner(resource, errors, resource_clone_context)
                # if resource:
                #     # attach to package_dict
                #     package_dict['resources'].append(resource)

                resource = toolkit.get_action('resource_create')(context, resource)
                
                # now let's clone the views
                views = toolkit.get_action('resource_view_list')(None,{'id': _resource['id']})
                for view in views:
                    view_dict_clone = {
                        'view_type': view['view_type'],
                        'title': view['title'],
                        'resource_id': resource['id']
                    }

                    # TODO how to clone other custom views?

                    # this cloner will take care of normal views
                    # AND jsonschema views
                    jsonschema_type = view.get('jsonschema_type')

                    if jsonschema_type:
                        view_dict_clone.update({
                            _c.SCHEMA_BODY_KEY: view.get('jsonschema_body'),
                            _c.SCHEMA_TYPE_KEY: jsonschema_type,
                            _c.SCHEMA_OPT_KEY: view.get('jsonschema_opt')
                        })

                    try:
                        vv = toolkit.get_action('resource_view_create')(context, view_dict_clone)
                    except Exception as e:
                        log.error(str(e))
            
            except PluginNotFoundException: #TODO remove, should raise error
                log.error('Unable to find a plugin implementation for resource type {}'.format(resource_type))
                raise

        
        import ckanext.jsonschema.logic.action.action as action
        action.index_package({'package_id': new_pkg_dict.get('id')})

        return new_pkg_dict
        
    except Exception as e:
        import traceback
        traceback.print_exc()

        message = str(e)
        log.error(message)
        raise ValidationError(message)


@side_effect_free
def view_show(context, data_dict):
    
    view_id = data_dict.get('view_id')
    resolve = data_dict.get('resolve', False)

    _check_access('resource_view_show', context, {'id': view_id})

    query = 'view_ids:{}'.format(view_id)
    
    # commented out, not properly supported by solr 3.6
    # fl = 'view_*,indexed_ts'

    results = indexer.search(query=query)
    
    if len(results) == 0:
        raise NotFound('Unable to find view: {}'.format(view_id))

    log.debug('Search view result is: {}'.format(results))

    document = results.docs[0]

    found = False
    view_ids = document.get('view_ids')
    if view_ids:
        for idx, id in enumerate(view_ids):
            if id == view_id:
                found = True
                break

    if not found:
        raise NotFound('Unable to find view: {}'.format(view_id))

    view_document = _t.dictize_pkg(json.loads(document.get('view_jsonschemas')[idx]))

    if resolve:
        view_body = view_document.get('{}_resolved'.format(_c.SCHEMA_BODY_KEY))
    else:
        view_body = view_document.get(_c.SCHEMA_BODY_KEY) 

    content = {
        'indexed_ts': document.get('indexed_ts').isoformat(),
        'package_id': view_document.get('package_id'),
        'resource_id': view_document.get('resource_id'),
        'view_id': view_document.get('view_id'),
        'view_type': view_document.get('view_type'),
        _c.SCHEMA_TYPE_KEY: view_document.get(_c.SCHEMA_TYPE_KEY),
        _c.SCHEMA_BODY_KEY: view_body,
        _c.SCHEMA_OPT_KEY: view_document.get(_c.SCHEMA_OPT_KEY)
    }

    return content
    
def _append_param(data_dict, dict_key, q, solr_key):
    # , starred = True, quoted = False):
    solr_val = data_dict.get(dict_key)
    join_condition = data_dict.get('join_condition', 'and').lower()
    # if starred and quoted:
    #     value='"*{{}}*"'
    # elif starred:
    #     value='*{{}}*'
    # elif quoted:
    #     value='"{{}}"'
    if solr_val:
        # base_query = '{}:{}'.format()
        if q:
            # return '{} {} {}:"*{}*"'.format(q, join_condition, solr_key, solr_val), solr_val.lower()
            return '{} {} {}:{}'.format(q, join_condition, solr_key, solr_val), solr_val.lower()
        else:
            # return '{}:"*{}*"'.format(solr_key, solr_val), solr_val.lower()
            return '{}:{}'.format(solr_key, solr_val), solr_val.lower()

    return None, None


@side_effect_free
def view_list(context, data_dict):

    package_id = data_dict.get('package_id')
    if not package_id:
        raise ValidationError('Parameter \'package_id\' is mandatory')

    try:
        query = 'capacity:public'
        fq = 'id:{} OR name:{}'.format(package_id, package_id)

        results = indexer.search(query=query, fq=fq)
        
        returning = []
        
        # for each package
        if results:
            views = results[0].get('view_jsonschemas')
            if views:
                for view in views:
                    # if matching the view_type
                    # if searching_view_type in view_type:
                        # fetch the body
                    view_document = _t.dictize_pkg(json.loads(view))
                    returning.append(_view_model(view_document))
        
        return returning

    except Exception as e:
        raise ValidationError(str(e))

@side_effect_free
def view_search(context, data_dict):
    # view_jsonschema_types=terriajs # wms, csv, scorecard, mapcard 

    # view_types=terriajs #plugin name
    
    if 'view_type' not in data_dict:
        raise ValidationError('Parameter \'view_type\' (plugin name used as view type) is mandatory')
    searching_view_type = data_dict.get('view_type').lower()

    page_size = int(data_dict.get('page_size', 100))
    if page_size > 1000:
        raise ValidationError('Parameter \'page_size\' maximum value is 100, try refining your query parameter')

    offset =  data_dict.get('offset', 0)

    # The q parameter is going to be used for free text searching though the fileds,
    # the API should take query parametar for q searching
    query_text = data_dict.get('query')

    # notes
    # name
    # organization
    #

    try:
        model = context['model']
        session = context['session']
        user = context.get('user')

        # results should be returned according to user permissions
        if context.get('ignore_auth') or (user and authz.is_sysadmin(user)):
            labels = None
        else:
            labels = lib_plugins.get_permission_labels(
                ).get_user_dataset_labels(context['auth_user_obj'])

        # append permission labels
        fq = []
        if labels is not None:
            fq.append('+permission_labels:(%s)' % ' OR '.join(
                ckan_query.solr_literal(p) for p in labels))

        # check if query_text is not none
        if query_text is not None:
            query = '{} AND view_types:{}'.format(query_text, searching_view_type)
        else:
            query = 'view_types:{}'.format(searching_view_type)

        q = None
        # view_jsonschema the content
        (aq, searching_schema_type) = _append_param(data_dict, 'schema_type', q, 'view_jsonschema_types')
        q = aq if aq else q
        (aq, searching_organization_name) = _append_param(data_dict, 'organization_name', q, 'organization')
        q = aq if aq else q
        (aq, searching_package_name) = _append_param(data_dict, 'package_name', q, 'name')
        q = aq if aq else q
        (aq, searching_package_title) = _append_param(data_dict, 'package_title', q, 'title')
        q = aq if aq else q
        (aq, searching_package_desc) = _append_param(data_dict, 'package_desc', q, 'notes')
        q = aq if aq else q
        (aq, searching_res_name) = _append_param(data_dict, 'resource_name', q, 'res_name')
        q = aq if aq else q
        (aq, searching_res_desc) = _append_param(data_dict, 'resource_desc', q, 'res_description')
        q = aq if aq else q
        (aq, searching_tags) = _append_param(data_dict, 'tags', q, 'tags')
        q = aq if aq else q
        (aq, searching_res_type) = _append_param(data_dict, 'data_format', q, 'res_format')
        q = aq if aq else q        

        if q is not None:
            fq.append(q)

        # q = '+package_title'.format(data_dict.get('title','').lower()) if 'package_title' in data_dict else q

        # q = '+res_name'.format(data_dict.get('resource_title','').lower()) if 'resource_title' in data_dict else q
        # q = '+res_description'.format(data_dict.get('resource_desc','').lower()) if 'resource_desc' in data_dict else q
        
        # commented out, not properly supported by solr 3.6
        # fl = 'view_*,indexed_ts'
        solr_results = indexer.search(query=query, fq=fq or '', start=offset, rows=page_size)
        results = solr_results.docs
        count = solr_results.hits

        # log.debug('Search view result is: {}'.format(results))

        returning = []
        # view_matches
        total_views = 0
        
        # for each package
        for document in results:
            # create the result entry pkg dict
            result = []

            # add package and organization information to the response
            package_tmp = _t.dictize_pkg(json.loads(document.get('data_dict')))
            resources_tmp = package_tmp['resources']
            organization_tmp = package_tmp['organization']

            res_descs = document.get('res_description')
            res_names = document.get('res_name')
            # resources that have terrijs view?
            res_ids = document.get('res_ids')
            matching_res_id = []
            resources = []
            if searching_res_name and searching_res_desc:
                if res_names and res_descs:
                    if len(res_descs) == len(res_names):
                        join_condition = data_dict.get('join_condition', 'and').lower()
                        for ridx, res_name in enumerate(res_names):
                            res_desc = res_descs[ridx]

                            if join_condition=='and':
                                if searching_res_name in res_name.lower() and searching_res_desc in res_desc.lower():
                                    matching_res_id.append(res_ids[ridx])
                            else:
                                if searching_res_name in res_name.lower() or searching_res_desc in res_desc.lower():
                                    matching_res_id.append(res_ids[ridx])
                    else:
                        # descriptions and names lengths are not matching
                        # it's impossible to match by description also
                        # we will return all the views of this package ignoring the
                        # exact match with the description
                        matching_res_id = res_ids

            elif searching_res_name:
                if res_names:
                    for ridx, res_name in enumerate(res_names):
                        if searching_res_name in res_name.lower():
                            matching_res_id.append(res_ids[ridx])
            elif searching_res_desc:
                # should be mandatory while description is not
                # so res_id array lenght will most probably match with res_names
                # but we can't count on the same when you use description
                # let's try to match with res_names array
                if res_names and res_descs:
                    if len(res_descs) == len(res_names):
                        for ridx, res_desc in enumerate(res_descs):
                            if searching_res_desc in res_desc.lower():
                                matching_res_id.append(res_ids[ridx])
                else:
                    # descriptions and names lengths are not matching
                    # it's impossible to match by description also
                    # we will return all the views of this package ignoring the
                    # exact match with the description
                    matching_res_id = res_ids
            else:
                # no resource filter condition
                matching_res_id = res_ids
            
            if len(matching_res_id) > 0:
                for res_id in matching_res_id:
                    resource = next((d for d in resources_tmp if d.get('id') == res_id), None)
                    resources.extend(matching_views_by_package(document, resource, searching_view_type, res_id, searching_schema_type))

            # only particular fields of the organization data dictionary are shown for the results
            package_tmp['organization'] = {
                'id': organization_tmp['id'],
                'name': organization_tmp['name'],
                'title': organization_tmp['title'],
                'description': organization_tmp['description']
            }

            package_tmp.pop('resources', None)
            total_views += len(resources)
            package_tmp['views'] = resources
            package_tmp['num_resources_view'] = len(resources)
            result.append(package_tmp)

            returning.extend(result)

        pkg_count = len(returning)

        # generate the response
        search_results = {
            'total_package_count': count,
            'package_count': pkg_count,
            'view_count': total_views,
            'offset': offset,
            'packages': returning
        }

        return search_results
    except Exception as e:
        raise ValidationError(str(e))

def matching_views_by_package(document, resource, searching_view_type = None, res_id = None, searching_schema_type = None):
    ret = []
    view_types = document.get('view_types')
    # for each view
    if view_types:
        for vidx, view_type in enumerate(view_types):
            # if matching the view_type
            if searching_view_type in view_type:
                # fetch the body
                view_document = _t.dictize_pkg(json.loads(document.get('view_jsonschemas')[vidx]))

                # if res_id is passed we also have to filter by resource_id
                if res_id:
                    if res_id != view_document.get('resource_id'):
                        continue

                # filter by view schema type
                if searching_schema_type:
                    if searching_schema_type != view_document.get(_c.SCHEMA_TYPE_KEY):
                        continue

                view = _view_model_resource(view_document)
                for key in view:
                    if key not in resource.keys():
                        resource[key] = view[key]
                ret.append(resource)
    return ret

def matching_views(document, searching_view_type = None, res_id = None, searching_schema_type = None):
    ret = []
    view_types = document.get('view_types')
    # for each view
    if view_types:
        for vidx, view_type in enumerate(view_types):
            # if matching the view_type
            if searching_view_type in view_type:
                # fetch the body
                view_document = _t.dictize_pkg(json.loads(document.get('view_jsonschemas')[vidx]))

                # add package and organization information to the response
                view_document['package'] = []
                view_document['organization'] = []
                package_tmp = _t.dictize_pkg(json.loads(document.get('data_dict')))
                organization_tmp = package_tmp['organization']

                # only particular fields of the package data dictionary are shown for the results
                view_document['package'] = {
                    'id': package_tmp['id'],
                    'name': package_tmp['name'],
                    'title': package_tmp['title'],
                    'type': package_tmp['type'],
                    'notes': package_tmp['notes'],
                    'tags': package_tmp['tags'],
                    'license_id': package_tmp['license_id'],
                    'license_title': package_tmp['license_title'],
                    'author': package_tmp['author'],
                    'author_email': package_tmp['author_email'],
                    'maintainer': package_tmp['maintainer'],
                    'maintainer_email': package_tmp['maintainer_email'],
                    'creator_user_id': package_tmp['creator_user_id']
                }

                # only particular fields of the organization data dictionary are shown for the results
                view_document['organization'] = {
                    'id': organization_tmp['id'],
                    'name': organization_tmp['name'],
                    'title': organization_tmp['title'],
                    'description': organization_tmp['description']
                }

                # if res_id is passed we also have to filter by resource_id
                if res_id:
                    if res_id != view_document.get('resource_id'):
                        continue

                # filter by view schema type
                if searching_schema_type:
                    if searching_schema_type != view_document.get(_c.SCHEMA_TYPE_KEY):
                        continue
                # if here append the document
                ret.append(_view_model(view_document))

    return ret


def _view_model(view_document):

    package = view_document['package']
    organization = view_document['organization']
    package_id = view_document['package_id']
    resource_id = view_document['resource_id']
    view_id = view_document['view_id']

    return {
        'package': package,
        'organization': organization,
        'package_id': package_id,
        'resource_id': resource_id,
        'view_id': view_id,
        'resource_link': toolkit.url_for('/dataset/{}/resource/{}'\
            .format(package_id, resource_id), _external=True),
        'metadata_link': toolkit.url_for('/dataset/{}'.format(package_id), _external=True),
        '{}_link'.format(_c.SCHEMA_BODY_KEY): toolkit.url_for('/{}/body/{}/{}/{}'\
            .format(_c.TYPE, package_id, resource_id, view_id),  _external=True, resolve=True),
        'view_type': view_document.get('view_type'),
        _c.SCHEMA_BODY_KEY: view_document.get('{}_resolved'.format(_c.SCHEMA_BODY_KEY)),
        _c.SCHEMA_TYPE_KEY: view_document.get(_c.SCHEMA_TYPE_KEY),
        _c.SCHEMA_OPT_KEY: view_document.get(_c.SCHEMA_OPT_KEY)
    }

def _view_model_resource(view_document):
    package_id = view_document['package_id']
    resource_id = view_document['resource_id']
    view_id = view_document['view_id']

    return {
        'view_id': view_id,
        'resource_link': toolkit.url_for('/dataset/{}/resource/{}'\
            .format(package_id, resource_id), _external=True),
        'metadata_link': toolkit.url_for('/dataset/{}'.format(package_id), _external=True),
        '{}_link'.format(_c.SCHEMA_BODY_KEY): toolkit.url_for('/{}/body/{}/{}/{}'\
            .format(_c.TYPE, package_id, resource_id, view_id),  _external=True, resolve=True),
        'view_type': view_document.get('view_type'),
        _c.SCHEMA_BODY_KEY: view_document.get('{}_resolved'.format(_c.SCHEMA_BODY_KEY)),
        _c.SCHEMA_TYPE_KEY: view_document.get(_c.SCHEMA_TYPE_KEY),
        _c.SCHEMA_OPT_KEY: view_document.get(_c.SCHEMA_OPT_KEY)
    }