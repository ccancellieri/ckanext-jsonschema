from datetime import date
import re
import six
from six.moves.urllib.parse import urlparse, urlunparse, urlencode

from lxml import etree
import json
from ckan import logic
from ckan import model
from ckan import plugins as p
from ckantoolkit import config

from ckan.lib.navl.validators import not_empty
from ckan.plugins.core import SingletonPlugin

# IHarvester

# from ckanext.spatial.harvesters.iso19115.model import ISO19115Document
from ckanext.harvest.interfaces import IHarvester
from ckanext.harvest.harvesters.base import HarvesterBase
from ckanext.harvest.model import HarvestObject
from ckanext.harvest.model import HarvestObjectExtra as HOExtra


from ckanext.jsonschema.iso19139.csw_client import CswService

import logging
log = logging.getLogger(__name__)

def text_traceback():
    import warnings
    import cgitb
    import sys
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = 'the original traceback:'.join(
            cgitb.text(sys.exc_info()).split('the original traceback:')[1:]
        ).strip()
    return res

class HarvesterIso19139(HarvesterBase, SingletonPlugin):
    p.implements(IHarvester, inherit=True)

    csw_harvester = None

    _user_name = None

    _site_user = None

    source_config = {}

    force_import = False

    from string import Template
    extent_template = Template('''
    {"type": "Polygon", "coordinates": [[[$xmin, $ymin], [$xmax, $ymin], [$xmax, $ymax], [$xmin, $ymax], [$xmin, $ymin]]]}
    ''')

    def _get_csw_harvester(self):
        if not self.csw_harvester:
            try:
                self.csw_harvester = p.get_plugin('csw_harvester')
            except Exception as e:
                log.error('Failed to get package from base implementation:\n%r', str(e))
                raise e

        return self.csw_harvester

    def _get_validators(self):
        '''
        Allows to register custom Validators that can be applied to harvested
        metadata documents.

        Validators are classes that implement the ``is_valid`` method. Check
        the `Writing custom validators`_ section in the docs to know more
        about writing custom validators.

        :returns: A list of Validator classes
        :rtype: list
        '''
        # import ckanext.jsonschema.iso19139.validators as validators
        # return [
        #           validators.ISO19115_Schema,
        #           validators.ISO19115_2_Schema,
        #           validators.ISO19115_1_Schema,
        #           validators.ISO19115_Schematron ]
        return []


    def info(self):
        return {
            'name': 'harvester_iso19139',
            'title': 'new ISO19139 CSW+JSONSchema based',
            'description': ''
            }

#################################################################

# IHarvester

    # CSWHarvester
    def _setup_csw_client(self, url):
        self.csw = CswService(url)

    # CSWHarvester
    # From parent SpatialHarvester

    def validate_config(self, source_config):
        #     all_validators = (ISO19139Schema,
        #               ISO19139EdenSchema,
        #               ISO19139NGDCSchema,
        #               FGDCSchema,
        #               ConstraintsSchematron,
        #               ConstraintsSchematron14,
        #               Gemini2Schematron,
        #               Gemini2Schematron13)

        if not source_config:
            return source_config

        try:
            source_config_obj = json.loads(source_config)

            if 'validator_profiles' in source_config_obj:
                if not isinstance(source_config_obj['validator_profiles'], list):
                    raise ValueError('validator_profiles must be a list')

                # # Check if all profiles exist
                # existing_profiles = [v.name for v in all_validators]
                # unknown_profiles = set(source_config_obj['validator_profiles']) - set(existing_profiles)

                # if len(unknown_profiles) > 0:
                #     raise ValueError('Unknown validation profile(s): %s' % ','.join(unknown_profiles))

            if 'default_tags' in source_config_obj:
                if not isinstance(source_config_obj['default_tags'],list):
                    raise ValueError('default_tags must be a list')

            if 'default_extras' in source_config_obj:
                if not isinstance(source_config_obj['default_extras'],dict):
                    raise ValueError('default_extras must be a dictionary')

            for key in ('override_extras', 'clean_tags'):
                if key in source_config_obj:
                    if not isinstance(source_config_obj[key],bool):
                        raise ValueError('%s must be boolean' % key)

        except ValueError as e:
            raise e

        return source_config

    # Delegate to CSWHarvester
    def get_original_url(self, harvest_object_id):
        '''
        [optional]

        This optional but very recommended method allows harvesters to return
        the URL to the original remote document, given a Harvest Object id.
        Note that getting the harvest object you have access to its guid as
        well as the object source, which has the URL.
        This URL will be used on error reports to help publishers link to the
        original document that has the errors. If this method is not provided
        or no URL is returned, only a link to the local copy of the remote
        document will be shown.

        Examples:
            * For a CKAN record: http://{ckan-instance}/api/rest/{guid}
            * For a WAF record: http://{waf-root}/{file-name}
            * For a CSW record: http://{csw-server}/?Request=GetElementById&Id={guid}&...

        :param harvest_object_id: HarvestObject id
        :returns: A string with the URL to the original document
        '''
        # FROM CSWHarvester
        obj = model.Session.query(HarvestObject).\
                            filter(HarvestObject.id==harvest_object_id).\
                            first()

        parts = urlparse(obj.source.url)

        params = {
            'SERVICE': 'CSW',
            'VERSION': '2.0.2',
            'REQUEST': 'GetRecordById',
            'OUTPUTSCHEMA': 'http://www.isotc211.org/2005/gmd',
            'OUTPUTFORMAT':'application/xml' ,
            'ID': obj.guid
        }

        url = urlunparse((
            parts.scheme,
            parts.netloc,
            parts.path,
            None,
            urlencode(params),
            None
        ))

        return url


    def output_schema(self):
        return 'gmd'

    # overriding waiting for merge ckanext-spatial #258
    def gather_stage(self, harvest_job):
        '''
        The gather stage will receive a HarvestJob object and will be
        responsible for:
            - gathering all the necessary objects to fetch on a later.
              stage (e.g. for a CSW server, perform a GetRecords request)
            - creating the necessary HarvestObjects in the database, specifying
              the guid and a reference to its job. The HarvestObjects need a
              reference date with the last modified date for the resource, this
              may need to be set in a different stage depending on the type of
              source.
            - creating and storing any suitable HarvestGatherErrors that may
              occur.
            - returning a list with all the ids of the created HarvestObjects.
            - to abort the harvest, create a HarvestGatherError and raise an
              exception. Any created HarvestObjects will be deleted.

        :param harvest_job: HarvestJob object
        :returns: A list of HarvestObject ids
        '''
        # FROM CSWHarvester
        log = logging.getLogger(__name__ + '.CSW.gather')
        log.debug('CswHarvester gather_stage for job: %r', harvest_job)
        # Get source URL
        url = harvest_job.source.url

        self._set_source_config(harvest_job.source.config)

        try:
            self._setup_csw_client(url)
        except Exception as e:
            self._save_gather_error('Error contacting the CSW server: %s' % e, harvest_job)
            return None

        query = model.Session.query(HarvestObject.guid, HarvestObject.package_id).\
                                    filter(HarvestObject.current==True).\
                                    filter(HarvestObject.harvest_source_id==harvest_job.source.id)
        guid_to_package_id = {}

        for guid, package_id in query:
            guid_to_package_id[guid] = package_id

        guids_in_db = set(guid_to_package_id.keys())

        # extract cql filter if any
        cql = self.source_config.get('cql')

        log.debug('Starting gathering for %s' % url)
        guids_in_harvest = set()
        try:
            for identifier in self.csw.getidentifiers(page=10, outputschema=self.output_schema(), cql=cql):
                try:
                    log.info('Got identifier %s from the CSW', identifier)
                    if identifier is None:
                        log.error('CSW returned identifier %r, skipping...' % identifier)
                        continue

                    guids_in_harvest.add(identifier)
                except Exception as e:
                    self._save_gather_error('Error for the identifier %s [%r]' % (identifier,e), harvest_job)
                    continue

        except Exception as e:
            log.error('Exception: %s' % text_traceback())
            self._save_gather_error('Error gathering the identifiers from the CSW server [%s]' % six.text_type(e), harvest_job)
            return None

        new = guids_in_harvest - guids_in_db
        delete = guids_in_db - guids_in_harvest
        change = guids_in_db & guids_in_harvest

        ids = []
        for guid in new:
            obj = HarvestObject(guid=guid, job=harvest_job,
                                extras=[HOExtra(key='status', value='new')])
            obj.save()
            ids.append(obj.id)
        for guid in change:
            obj = HarvestObject(guid=guid, job=harvest_job,
                                package_id=guid_to_package_id[guid],
                                extras=[HOExtra(key='status', value='change')])
            obj.save()
            ids.append(obj.id)
        for guid in delete:
            obj = HarvestObject(guid=guid, job=harvest_job,
                                package_id=guid_to_package_id[guid],
                                extras=[HOExtra(key='status', value='delete')])
            model.Session.query(HarvestObject).\
                  filter_by(guid=guid).\
                  update({'current': False}, False)
            obj.save()
            ids.append(obj.id)

        if len(ids) == 0:
            self._save_gather_error('No records received from the CSW server', harvest_job)
            return None

        return ids
        
    
    def _set_source_config(self, config_str):
        '''
        Loads the source configuration JSON object into a dict for
        convenient access
        '''
        if config_str:
            self.source_config = json.loads(config_str)
            log.debug('Using config: %r', self.source_config)
        else:
            self.source_config = {}

    
    def _is_wms(self, url):
        '''
        Checks if the provided URL actually points to a Web Map Service.
        Uses owslib WMS reader to parse the response.
        '''
        try:
            from owslib import wms
            s = wms.WebMapService(url)
            return isinstance(s.contents, dict) and s.contents != {}
        except Exception as e:
            log.error('WMS check for %s failed with exception: %s' % (url, six.text_type(e)))
        return False

    def _get_object_extra(self, harvest_object, key):
        '''
        Helper function for retrieving the value from a harvest object extra,
        given the key
        '''
        for extra in harvest_object.extras:
            if extra.key == key:
                return extra.value
        return None
        
    # overriding waiting for merge ckanext-spatial #258
    def fetch_stage(self,harvest_object):
        '''
        The fetch stage will receive a HarvestObject object and will be
        responsible for:
            - getting the contents of the remote object (e.g. for a CSW server,
            perform a GetRecordById request).
            - saving the content in the provided HarvestObject.
            - creating and storing any suitable HarvestObjectErrors that may
            occur.
            - returning True if everything is ok (ie the object should now be
            imported), "unchanged" if the object didn't need harvesting after
            all (ie no error, but don't continue to import stage) or False if
            there were errors.

        :param harvest_object: HarvestObject object
        :returns: True if successful, 'unchanged' if nothing to import after
                all, False if not successful
        '''
        # FROM CSWHarvester

        # Check harvest object status
        status = self._get_object_extra(harvest_object, 'status')

        if status == 'delete':
            # No need to fetch anything, just pass to the import stage
            return True

        log = logging.getLogger(__name__ + '.CSW.fetch')
        log.debug('CswHarvester fetch_stage for object: %s', harvest_object.id)

        url = harvest_object.source.url
        try:
            self._setup_csw_client(url)
        except Exception as e:
            self._save_object_error('Error contacting the CSW server: %s' % e,
                                    harvest_object)
            return False
        
        # load config
        self._set_source_config(harvest_object.source.config)
        # get output_schema from config
        output_schema = self.source_config.get('output_schema',self.output_schema())
        identifier = harvest_object.guid
        try:
            record = self.csw.getrecordbyid([identifier], outputschema=output_schema)
        except Exception as e:
            try:
                log.warn('Unable to fetch GUID {} with output schema: {}'.format(identifier, output_schema))
                if output_schema == self.output_schema():
                    raise e
                log.info('Fetching GUID {} with output schema: {}'.format(identifier, self.output_schema()))
                # retry with default output schema
                record = self.csw.getrecordbyid([identifier], outputschema=self.output_schema())
            except Exception as e:
                self._save_object_error('Error getting the CSW record with GUID {}'.format(identifier), harvest_object)
                return False
        
        if record is None:
            self._save_object_error('Empty record for GUID %s' % identifier,
                                    harvest_object)
            return False

        try:
            # Save the fetch contents in the HarvestObject
            # Contents come from csw_client already declared and encoded as utf-8
            # Remove original XML declaration
            content = re.sub('<\?xml(.*)\?>', '', record['xml'])

            harvest_object.content = content.strip()
            harvest_object.save()
        except Exception as e:
            self._save_object_error('Error saving the harvest object for GUID %s [%r]' % \
                                    (identifier, e), harvest_object)
            return False

        log.debug('XML content saved (len %s)', len(record['xml']))
        return True

    # From parent IHarvester
    def import_stage(self, harvest_object):
        '''
        The import stage will receive a HarvestObject object and will be
        responsible for:
            - performing any necessary action with the fetched object (e.g.
              create, update or delete a CKAN package).
              Note: if this stage creates or updates a package, a reference
              to the package should be added to the HarvestObject.
            - setting the HarvestObject.package (if there is one)
            - setting the HarvestObject.current for this harvest:
               - True if successfully created/updated
               - False if successfully deleted
            - setting HarvestObject.current to False for previous harvest
              objects of this harvest source if the action was successful.
            - creating and storing any suitable HarvestObjectErrors that may
              occur.
            - creating the HarvestObject - Package relation (if necessary)
            - returning True if the action was done, "unchanged" if the object
              didn't need harvesting after all or False if there were errors.

        NB You can run this stage repeatedly using 'paster harvest import'.

        :param harvest_object: HarvestObject object
        :returns: True if the action was done, "unchanged" if the object didn't
                  need harvesting after all or False if there were errors.
        '''

        log = logging.getLogger(__name__ + '.import')
        log.debug('Import stage for harvest object: %s', harvest_object.id)

        # check arguments
        if not harvest_object:
            log.error('No harvest object received')
            return False
        elif harvest_object.content is None:
            self._save_object_error('Empty content for object {0}'.format(harvest_object.id), harvest_object, 'Import')
            return False


        # read configuration
        self._set_source_config(harvest_object.source.config)

        # prepare context
        context = {
            'model': model,
            'session': model.Session,
            'user': self._get_user_name(),
            # Tunnelled to pass to spatial_plugin
            'config': dict(self.source_config)
        }

        # Flag previous object as not current anymore
        # Get the last harvested object (if any)
        previous_object = model.Session.query(HarvestObject) \
                            .filter(HarvestObject.guid==harvest_object.guid) \
                            .filter(HarvestObject.current==True) \
                            .first()
                            
        if previous_object and not self.force_import:
            previous_object.current = False
            previous_object.add()

        ##############################################

        # evaluate the new status
        if self.force_import:
            status = 'change'
        else:
            status = self._get_object_extra(harvest_object, 'status')

        if status == 'delete':
            return self._delete(context, harvest_object)

        ###################
        # TODO guess the 'right' ISpatialHarvester
        
        # Validate ISO document
        is_valid, _status, _plugin, _validator = self._validate(harvest_object)
        if not is_valid:
            # If validation errors were found, import will stop unless
            # harvester validation flag says otherwise
            # TODO better policy, based on cumulated _status
            if not self.source_config.get('continue_on_validation_errors') \
                    and \
                    not p.toolkit.asbool(config.get('ckanext.spatial.harvest.continue_on_validation_errors', False)):
                return False
        # Build the package dict    
        
        ################## TODO ###############
        package_dict = harvest_object.content
    # def __init__(self, xml_str=None, xml_tree=None):
    #     assert (xml_str or xml_tree is not None), 'Must provide some XML in one format or another'
    #     self.xml_str = xml_str
    #     self.xml_tree = xml_tree

    # def read_values(self):
    #     '''For all of the elements listed, finds the values of them in the
    #     XML and returns them.'''
    #     values = {}
    #     tree = self.get_xml_tree()
    #     for element in self.elements:
    #         values[element.name] = element.read_value(tree)
    #     self.infer_values(values)
    #     return values

        # package_dict={
        #     _c.SCHEMA_BODY_KEY:
        # }

        if not package_dict:
            log.error('No package dict returned, aborting import for object {0}'.format(harvest_object.id))
            return False

        # namespaces = {u'http://www.opengis.net/gml/3.2': u'gml', u'http://www.isotc211.org/2005/srv': u'srv', u'http://www.isotc211.org/2005/gts': u'gts', u'http://www.isotc211.org/2005/gmx': u'gmx', u'http://www.isotc211.org/2005/gmd': u'gmd', u'http://www.isotc211.org/2005/gsr': u'gsr', u'http://www.w3.org/2001/XMLSchema-instance': u'xsi', u'http://www.isotc211.org/2005/gco': u'gco', u'http://www.isotc211.org/2005/gmi': u'gmi', u'http://www.w3.org/1999/xlink': u'xlink'}
        # # TODO DEBUG

        # _namespaces=_j['http://www.isotc211.org/2005/gmd:MD_Metadata']['@xmlns']
        # namespaces = dict((v,k) for k,v in _namespaces.iteritems())
        # # _u.json_to_xml()
        # _u.xml_to_json(package_dict, namespaces)
   

        # Update GUID with the one on the document
        #iso_guid = package_dict.get('guid')
        self._set_guid(harvest_object, None)
        
        # # Get document modified date
        # metadata_date = package_dict.get('metadata-date')
        # if metadata_date:
        #     import dateutil
        #     try:
        #         harvest_object.metadata_modified_date = dateutil.parser.parse(metadata_date, ignoretz=True)
        #     except ValueError:
        #         self._save_object_error('Could not extract reference date for object {0} ({1})'
        #                     .format(harvest_object.id, package_dict['metadata-date']), harvest_object, 'Import')
        #         return False
        # else:
        #     import datetime
        #     #TODO log warn!
        #     harvest_object.metadata_modified_date = datetime.datetime.today()


        ###################
        # TODO

        import ckanext.jsonschema.utils as _u
        import ckanext.jsonschema.constants as _c
        import os
        j = _u.xml_to_json(package_dict)

        package_dict={}
        package_dict['type']='iso'

        import json
        package_dict[_c.SCHEMA_BODY_KEY]=j
        package_dict[_c.SCHEMA_OPT_KEY]=json.dumps({'harvested' : True})
        package_dict[_c.SCHEMA_VERSION_KEY]=_c.SCHEMA_VERSION
        package_dict[_c.SCHEMA_TYPE_KEY]='iso'

        # We need to get the owner organization (if any) from the harvest
        # source dataset
        source_dataset = model.Package.get(harvest_object.source.id)
        if source_dataset.owner_org:
            package_dict['owner_org'] = source_dataset.owner_org
        
        ###################

        # context['user']=self.source_config.get('user','')

        # TODO doublecheck when to .add()
        # Flag this object as the current one
        harvest_object.current = True
        harvest_object.add()

        try:
            if status == 'new':
                # undelete
                package_dict['state']='active'
                # package_schema['tags'] = tag_schema
                return self._new(context, log, harvest_object, package_dict)

            else:
                if status == 'change':
                    # TODO restore if deleted
                    if harvest_object.package and harvest_object.package.state=='deleted':
                        # undelete
                        package_dict['state']='active'

                        # update
                        self._change(context, log, harvest_object, package_dict)

                    # Check if the modified date is more recent
                    elif not self.force_import \
                            and previous_object and \
                            harvest_object.metadata_modified_date <= previous_object.metadata_modified_date:
                        log.info('Document with GUID %s unchanged, skipping...' % (harvest_object.guid))
                        # Assign the previous job id to the new object to
                        # avoid losing history
                        harvest_object.harvest_job_id = previous_object.job.id
                        harvest_object.add()
                        # Delete the previous object to avoid cluttering the object table
                        previous_object.delete()
                    else:
                        # update
                        self._change(context, log, harvest_object, package_dict)

                self._index(context, log, harvest_object, package_dict)
        except p.toolkit.ValidationError as e:
            log.error('Error: {} unchanged, skipping...'.format(str(e)))
            self._save_object_error('Error: %s' % six.text_type(e.error_summary), harvest_object, 'Import')
            model.Session.rollback()
            model.Session.close()
            return False 
        else:
            model.Session.commit()
            return True

    def _set_guid(self, harvest_object, iso_guid):
        import uuid
        import hashlib
        if iso_guid and harvest_object.guid != iso_guid:
            # First make sure there already aren't current objects
            # with the same guid
            existing_object = model.Session.query(HarvestObject.id) \
                            .filter(HarvestObject.guid==iso_guid) \
                            .filter(HarvestObject.current==True) \
                            .first()
            if existing_object:
                self._save_object_error('Object {0} already has this guid {1}'.format(existing_object.id, iso_guid),
                        harvest_object, 'Import')
                return False

            harvest_object.guid = iso_guid
            harvest_object.add()

        # Generate GUID if not present (i.e. it's a manual import)
        if not harvest_object.guid:
            m = hashlib.md5()
            m.update(harvest_object.content)
            harvest_object.guid = m.hexdigest()
            harvest_object.add() #????

    def _validate(self, harvest_object):
        '''
            :returns: [True|False] status plugin_name
            if True some validator has passed (first win)
             in that case also the plugin is passed
             (True, status[plugin_name]['errors'], plugin, validator)
            if False the plugin name is false and a report 
             can be located under:
             status[plugin_name]['errors']
        '''
        # Add any custom validators from extensions
        is_valid = False

        return is_valid, {}, None, None

    def _delete(self, log, context, harvest_object):
        # Delete package
        context.update({
            'ignore_auth': True,
        })
        p.toolkit.get_action('package_delete')(context, {'id': harvest_object.package_id})
        log.info('Deleted package {0} with guid {1}'.format(harvest_object.package_id, harvest_object.guid))
        return True

    def _change(self, context, log, harvest_object, package_dict):
        package_dict['id'] = harvest_object.package_id
        package_id = p.toolkit.get_action('package_update')(context, package_dict)
        log.info('Updated package %s with guid %s', package_id, harvest_object.guid)

    def _index(self, context, log, harvest_object, package_dict):

        # Reindex the corresponding package to update the reference to the
        # harvest object
        if ((config.get('ckanext.spatial.harvest.reindex_unchanged', True) != 'False'
            or self.source_config.get('reindex_unchanged') != 'False')
            and harvest_object.package_id):
            context.update({'validate': False, 'ignore_auth': True})
            try:
                package_dict = logic.get_action('package_show')(context,
                    {'id': harvest_object.package_id})
            except p.toolkit.ObjectNotFound:
                # TODO LOG?!?!
                pass
            else:
                for extra in package_dict.get('extras', []):
                    if extra['key'] == 'harvest_object_id':
                        extra['value'] = harvest_object.id
                if package_dict:
                    from ckan.lib.search.index import PackageSearchIndex
                    PackageSearchIndex().index_package(package_dict)
        
    def _new(self, context, log, harvest_object, package_dict):

        if 'schema' in context:
            context.pop('schema')

        # We need to explicitly provide a package ID, otherwise ckanext-spatial
        # won't be be able to link the extent to the package.
        import uuid
        package_dict['id'] = six.text_type(uuid.uuid4())
        # package_schema['id'] = [six.text_type]
        try:
            package = p.toolkit.get_action('package_create')(context, package_dict)
        except Exception as e:
            log.error('Failed to harvest guid {}: {}'.format(harvest_object.guid, str(e)))
            # model.Session.rollback()
            # model.Session.close()
            return False
        else:
            # Save reference to the package on the object
            harvest_object.package_id = package['id']
            harvest_object.add()
            # Defer constraints and flush so the dataset can be indexed with
            # the harvest object id (on the after_show hook from the harvester
            # plugin)
            model.Session.execute('SET CONSTRAINTS harvest_object_package_id_fkey DEFERRED')
            model.Session.flush()
            
            log.info('Created new package %s with guid %s', package['id'], harvest_object.guid)
            return True
