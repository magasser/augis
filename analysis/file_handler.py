"""
Authors: Manuel Gasser, Julian Haldimann
Created: 16.03.2021
Last Modified: 01.05.2021
"""

import json

import requests
from shapely.geometry.polygon import Polygon

"""
Read GeoJson File from a route and map it into a list of coordinates.

:param payload: GeoJson String
:returns: An array filled with Positions
"""


def parse_route_geojson(payload):
    gj = json.loads(payload)

    return [(c[1], c[0]) for c in gj['features'][0]['geometry']['coordinates'][0]]


"""
Read GeoJson File from a lake and map it into a list of points.

:param payload: GeoJson String
:returns: Polygon of the lake
"""


def parse_lake_geojson(payload):
    gj = json.loads(payload)

    # Swap lat and lng values from lng,lat in geojson to lat,lng for our points
    exterior = [(p[1], p[0]) for p in gj['features'][0]['geometry']['coordinates'][0][0]]
    interior = [(p[1], p[0]) for p in gj['features'][1]['geometry']['coordinates'][0][0]]

    obstacles = []
    """for i in range(2, len(gj['features'])):
        print(i)
        poly = [(p[1], p[0]) for p in gj['features'][i]['geometry']['coordinates'][0][0]]
        obstacles.append(Polygon(poly))
    """
    exterior = Polygon(exterior)
    interior = Polygon(interior)
    return exterior, interior, obstacles

"""
Create geojson formatted data structure from GPS points.

:param points: to be included in the .geojson
:return: geojson formatted data structure
"""


def create_geojson(points, name):
    gj = {
        "type": "FeatureCollection",
        "name": name,
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
            }
        },
        "features": []
    }
    feature = {
        "type": "Feature",
        "properties": {
            "id": 1
        },
        "geometry": {
            "type": "MultiLineString",
            "coordinates": [[]],
        },
    }
    for point in points:
        feature["geometry"]["coordinates"][0].append([point[1], point[0]])
    gj["features"].append(feature)

    return gj
