#!/usr/bin/python
# -*- coding: utf-8 -*-

from math import radians, cos, sin, asin, sqrt
import requests
import codecs
import json
import os
import time

dir = os.path.abspath(os.path.dirname(__file__))

# Variables

LATITUDE = 48.8708161
LONGITUDE = 2.3472812
HIPCHAT_API_KEY = 'xxxxxxxx'
HIPCHAT_ROOM = 'PokemonGo'
LOCALE = 'fr'
MAX_DISTANCE = 70 #meters
CACHE_FILE = os.path.join(dir, 'cache.json') #to store previous run
POKEMON_IDS_TO_FILTER = [13, 16, 19, 21, 41]


# Loading Pokemons names
pokemonsJSON = json.load(codecs.open(os.path.join(dir,'locales/pokemon.' + LOCALE + '.json'), 'r', 'UTF-8'))


# Helper functions

def lonlat_to_meters(lat1, lon1, lat2, lon2):  
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    # earth radius in meters: 6378100
    m = 6378100 * c
    return m

def get_latest_pokemons(LATITUDE, LONGITUDE):
    url = "https://pokevision.com/map/data/%s/%s" % (LATITUDE, LONGITUDE)
    print 'API call: ' + url
    headers = {'application/json': 'application/json'}
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code == 200 and r.json().get('status') == 'success':
        return r.json().get('pokemon', [])
    else:
        raise IOError('API error when calling (status code %s):\n%s' % (r.status_code, r.text))

def notif_hipchat_new_pokemon(pokemon):
    name = pokemonsJSON.get(str(pokemon['pokemonId']), 'Unknown')
    distance = int(lonlat_to_meters(LATITUDE, LONGITUDE, pokemon['latitude'], pokemon['longitude']))
    seconds = pokemon['expiration_time'] - time.time()
    params = {
      'auth_token': HIPCHAT_API_KEY,
      'room_id': HIPCHAT_ROOM,
      'from': 'Pokevision',
      'color': 'purple',
      'notify': '1',
      'message_format': 'text',
      'message': 'New pokemon available: %s (%i meters) for %i seconds' % (name, distance, seconds)
    }
    #print params
    r = requests.get("https://api.hipchat.com/v1/rooms/message", params=params)



pokemons = get_latest_pokemons(LATITUDE, LONGITUDE)

nearest_pokemons = [pokemon for pokemon in pokemons if lonlat_to_meters(LATITUDE, LONGITUDE, pokemon['latitude'], pokemon['longitude']) <= MAX_DISTANCE]

print nearest_pokemons

# Load cache file
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)
        f.close()
else:
    cache = []

# Test if new pokemon available
cache_coordinates = set((p['latitude'], p['longitude']) for p in cache) #because the pokemon['id'] seems not to be really stable, we test against coordinates
for pokemon in nearest_pokemons:
    if (pokemon['latitude'], pokemon['longitude']) not in cache_coordinates:
    #if pokemon['id'] not in cache:
        if pokemon['pokemonId'] not in POKEMON_IDS_TO_FILTER:
            print "New pokemon: %s" % json.dumps(pokemon)
            notif_hipchat_new_pokemon(pokemon)

# Write json cache
cache = nearest_pokemons
#cache = [pokemon['id'] for pokemon in nearest_pokemons]
with open(CACHE_FILE, 'w') as f:
    json.dump(cache, f)
    f.close()
