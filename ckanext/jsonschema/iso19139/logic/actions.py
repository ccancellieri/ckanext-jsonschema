


from sqlalchemy.sql.operators import as_
from sqlalchemy.sql.sqltypes import ARRAY, TEXT
import ckan.plugins as plugins
import ckanext.terriajs.constants as constants

from ckan.model.resource_view import ResourceView
from ckan.model.resource import Resource
from ckan.model.package import Package
from ckan.model.core import State

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql.expression import cast
from sqlalchemy import func, Integer
from sqlalchemy.sql import select


import ckan.plugins.toolkit as toolkit
_ = toolkit._
h = toolkit.h

import ckan.logic as logic

_check_access = logic.check_access

@plugins.toolkit.chained_action
def import_iso19139(next_action, context, data_dict):
    
    if not data_dict:
        error_msg = 'No dict provided'
        h.flash_error(error_msg,allow_html=True)
        return

    return next_action(context,data_dict)