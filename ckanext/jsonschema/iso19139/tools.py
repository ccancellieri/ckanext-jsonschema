from six import text_type, string_types


def calculate_bbox(wms_base_url, layer_name = None):
    try:
        from owslib.wms import WebMapService
        from shapely import geometry
        from shapely.geometry import Polygon

        wms = WebMapService(wms_base_url)
        polygon = Polygon()
        bounds = (-180.0, -90.0, 180.0, 90.0)

        if layer_name:
            if isinstance(layer_name, list):
                for layer in layer_name:
                    if layer in wms.contents.keys():
                        bbox = wms.contents[layer].boundingBoxWGS84
                        polygon = polygon.union(geometry.box(*bbox, ccw=True))
                        bounds = polygon.bounds
            elif isinstance(layer_name, text_type):

                bounds = wms.contents[layer_name].boundingBoxWGS84
        else:
            for layer in layer in wms.contents.keys():
                bbox = wms.contents[layer].boundingBoxWGS84
                polygon = polygon.union(geometry.box(*bbox, ccw=True))
            bounds = polygon.bounds
            # return (-180.0, -90.0, 180.0, 90.0)
    except:
        pass
    finally:
        return bounds or (-180.0, -90.0, 180.0, 90.0)


def params_for_solr_search(bbox, search_params):
        '''
        This will add the following parameters to the query:
            defType - edismax (We need to define EDisMax to use bf)
            bf - {function} A boost function to influence the score (thus
                 influencing the sorting). The algorithm can be basically defined as:
                    2 * X / Q + T
                 Where X is the intersection between the query area Q and the
                 target geometry T. It gives a ratio from 0 to 1 where 0 means
                 no overlap at all and 1 a perfect fit
             fq - Adds a filter that force the value returned by the previous
                  function to be between 0 and 1, effectively applying the
                  spatial filter.
        '''

        variables =dict(
            x11=bbox['minx'],
            x12=bbox['maxx'],
            y11=bbox['miny'],
            y12=bbox['maxy'],
            x21='minx',
            x22='maxx',
            y21='miny',
            y22='maxy',
            area_search = abs(bbox['maxx'] - bbox['minx']) * abs(bbox['maxy'] - bbox['miny'])
        )

        bf = '''div(
                   mul(
                   mul(max(0, sub(min({x12},{x22}) , max({x11},{x21}))),
                       max(0, sub(min({y12},{y22}) , max({y11},{y21})))
                       ),
                   2),
                   add({area_search}, mul(sub({y22}, {y21}), sub({x22}, {x21})))
                )'''.format(**variables).replace('\n','').replace(' ','')

        search_params['fq_list'] = search_params.get('fq_list', [])
        search_params['fq_list'].append('{!frange incl=false l=0 u=1}%s' % bf)

        search_params['bf'] = bf
        search_params['defType'] = 'edismax'

        return search_params


def validate_bbox(bbox_values):
    '''
    Ensures a bbox is expressed in a standard dict.
    bbox_values may be:
           a string: "-4.96,55.70,-3.78,56.43"
           or a list [-4.96, 55.70, -3.78, 56.43]
           or a list of strings ["-4.96", "55.70", "-3.78", "56.43"]
    and returns a dict:
           {'minx': -4.96,
            'miny': 55.70,
            'maxx': -3.78,
            'maxy': 56.43}
    Any problems and it returns None.
    '''

    if isinstance(bbox_values, string_types):
        bbox_values = bbox_values.split(',')

    if len(bbox_values) != 4:
        return None

    try:
        bbox = {}
        bbox['minx'] = float(bbox_values[0])
        bbox['miny'] = float(bbox_values[1])
        bbox['maxx'] = float(bbox_values[2])
        bbox['maxy'] = float(bbox_values[3])
    except ValueError as e:
        return None

    return bbox



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