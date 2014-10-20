from math import radians, cos, sin, asin, sqrt
from config import geokey
import requests
import json


def geocode(address):
    uri = 'https://maps.googleapis.com/maps/api/geocode/json'
    payload = {'address': address, 'key': geokey}
    response = requests.get(uri, params=payload)
    data = json.loads(response.text)
    results = data['results']
    location = results[0]['geometry']['location']
    return location


def haversine(location1, location2):
    lng1 = location1['lng']
    lat1 = location1['lat']
    lng2 = location2['lng']
    lat2 = location2['lat']
    lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
    dlng = lng2 - lng1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    c = 2 * asin(sqrt(a))
    distance = 3959 * c
    return distance
