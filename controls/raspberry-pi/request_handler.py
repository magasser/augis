"""
Authors: Manuel Gasser, Julian Haldimann
Created: 21.03.2021
Last Modified: 01.05.2021
"""

import json

import requests

from config import Config

headers = {
    'Accept': '*/*',
    'Content-Type': 'application/json'
}

"""
Get route by id from the aws api.

:param id: of the route
"""


def get_route_by_id(id):
    res = requests.get(f"{Config.HOST}/api/routes/id/{id}", headers=headers)
    return res.json()


"""
Get lake by id from the aws api.

:param id: of the lake
"""


def get_lake_by_id(id):
    res = requests.get(f"{Config.HOST}/api/lakes/id/{id}", headers=headers)
    return res.json()


"""
Save route to database with aws api.

:param name: of the route
:param description: of the route
:param gj: json file containing the route
:param lake_id: id of the lake the route belongs to
"""


def save_route(name, description, gj, lake_id):
    data = {
        "name": name,
        "description": description,
        "json": gj,
        "lake": lake_id
    }

    json_data = {
        "data": json.dumps(data)
    }

    requests.post(f"{Config.HOST}/api/save-route", headers=headers, data=json.dumps(json_data))
