"""
            if self.search_backend == 'solr':
                # Only bbox supported for this backend
                if not (geometry['type'] == 'Polygon'
                   and len(geometry['coordinates']) == 1
                   and len(geometry['coordinates'][0]) == 5):
                    log.error('Solr backend only supports bboxes (Polygons with 5 points), ignoring geometry {0}'.format(pkg_dict['extras_spatial']))
                    return pkg_dict

                coords = geometry['coordinates']
                pkg_dict['maxy'] = max(coords[0][2][1], coords[0][0][1])
                pkg_dict['miny'] = min(coords[0][2][1], coords[0][0][1])
                pkg_dict['maxx'] = max(coords[0][2][0], coords[0][0][0])
                pkg_dict['minx'] = min(coords[0][2][0], coords[0][0][0])
                pkg_dict['bbox_area'] = (pkg_dict['maxx'] - pkg_dict['minx']) * \
                                        (pkg_dict['maxy'] - pkg_dict['miny'])


                bbox = Polygon()
                for every pacakge:
                    for every online-resource with format wms:
                        bounds = calculate_bbox(wms_base_url, resource_name/name)

                        bbox = bbox.union(geometry.box(*bounds, ccw=True))

                maxy, miny, maxx, minx = bbox.bounds
                pkg_dict['maxy'] = maxy
                pkg_dict['miny'] = miny
                pkg_dict['maxx'] = maxx
                pkg_dict['minx'] = minx
                pkg_dict['bbox_area'] = (pkg_dict['maxx'] - pkg_dict['minx']) * \
                                        (pkg_dict['maxy'] - pkg_dict['miny'])

                1 for pacakge

                <fields>
    <!-- ... -->
    <field name="bbox_area" type="float" indexed="true" stored="true" />
    <field name="maxx" type="float" indexed="true" stored="true" />
    <field name="maxy" type="float" indexed="true" stored="true" />
    <field name="minx" type="float" indexed="true" stored="true" />
    <field name="miny" type="float" indexed="true" stored="true" />
</fields>
"""



def calculate_bbox(wms_base_url, layer_name = None):
    try:
        from owslib import WebMapService
        wms = WebMapService(wms_base_url)
        from shapely import geometry
        from shapely.geometry import Polygon
        polygon = Polygon()
        if layer_name:
            if isinstance(layer_name, list):
                for layer in layer_name:
                    if layer in wms.contents.keys():
                        bbox = wms.contents[layer].boundingBoxWGS84
                        polygon = polygon.union(geometry.box(*bbox, ccw=True))
                        return polygon.bounds
            elif isinstance(layer_name, str):

                return wms.contents[layer_name].boundingBoxWGS84
        else:
            for layer in layer in wms.contents.keys():
                bbox = wms.contents[layer].boundingBoxWGS84
                polygon = polygon.union(geometry.box(*bbox, ccw=True))
            return polygon.bounds
            # return (-180.0, -90.0, 180.0, 90.0)
    except:
        return (-180.0, -90.0, 180.0, 90.0)


# TODO see also
# https://github.com/ckan/ckanext-spatial/blob/master/ckanext/spatial/lib/__init__.py
# https://github.com/ckan/ckanext-spatial/blob/master/ckanext/spatial/harvesters/base.py#L420
# https://geobgu.xyz/py/shapely.html
# https://github.com/ckan/ckanext-spatial/blob/992b2753fc24d0abb12ced5cf5aaa3a853ca9ea4/doc/spatial-search.rst


# response = wms.getmap(layers=[name,],
#                  styles=['rgb'],
#                  bbox=(-180, -90, 180, 90), # Left, bottom, right, top
#                  format='image/png',
#                  size=(600,600),
#                  srs='EPSG:4326',
#                  time='2018-09-16',
#                  transparent=True)
# response