import ckan.plugins.toolkit as toolkit
config = toolkit.config

import os
path = os.path


PATH_ROOT=path.realpath(path.dirname(__file__))

CONFIG_FILENAME = 'config.json'
PATH_CONFIG = path.realpath(config.get('ckanext.jsonschema_dashboard.path.config', path.join(PATH_ROOT, 'public')))
