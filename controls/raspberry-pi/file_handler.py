"""
Authors: Manuel Gasser, Julian Haldimann
Created: 16.03.2021
Last Modified: 01.05.2021
"""

import json

import requests
from shapely.geometry.polygon import Polygon

from config import Config

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
Convert points into geojson format and send it to the api to save 
it on the server.

:param name: of the route
:param description: of the route
:param points: of route to be converted and saved
"""


def save_geojson(name, description, points):
    gj = create_geojson(points)

    data = {
        "name": name,
        "filename": f"{name}.geojson",
        "description": description,
        "geojson": gj
    }
    json_data = {
        "data": json.dumps(data)
    }

    headers = {"Content-Type": "application/json"}

    requests.post(url=f"{Config.HOST}/api/save-route", headers=headers, data=json.dumps(json_data))


"""
Create geojson formatted data structure from GPS points.

:param points: to be included in the .geojson
:return: geojson formatted data structure
"""


def create_geojson(points):
    gj = {
        "type": "FeatureCollection",
        "features": []
    }
    for point in points:
        p = {
            "type": "Point",
            "coordinates": [point[1], point[0]]
        }
        gj["features"].append(p)

    return gj
