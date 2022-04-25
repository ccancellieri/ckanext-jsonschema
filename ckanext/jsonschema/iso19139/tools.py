
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


# response = wms.getmap(layers=[name,],
#                  styles=['rgb'],
#                  bbox=(-180, -90, 180, 90), # Left, bottom, right, top
#                  format='image/png',
#                  size=(600,600),
#                  srs='EPSG:4326',
#                  time='2018-09-16',
#                  transparent=True)
# response