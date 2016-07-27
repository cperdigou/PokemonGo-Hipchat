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

# geographic area restriction for notification
LATITUDE = 48.8709640
LONGITUDE = 2.34769463
MAX_DISTANCE = 70 #meters
# location(s) from which we want to calculate the distance
LOCATIONS = [
    {'main': [LATITUDE, LONGITUDE]},
    {'my room': [48.8712922, 2.3477321]},
    {'my kitchen': [48.8710593, 2.3469972]}
]
# hipchat
HIPCHAT_API_KEY = 'xxxxxxxx'
HIPCHAT_ROOM = 'PokemonGo'
# locale for pokemons name
LOCALE = 'fr'
# cache file
CACHE_FILE = os.path.join(dir, 'cache.json')
# to hide useless pokemons
POKEMON_IDS_TO_FILTER = [13, 16, 19, 21, 41]
WORTH_GOING_OUT = [3,6,9,26,28,31,34,36,57,59,91,94,95,101,112,114,115,128,139,141]
STOP_EVERYTHING_YOURE_DOING = [83,89,105,106,107,108,113,122,123,130,132,137,142,143,144,145,146,149,150,151]



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

def notif_hipchat_new_pokemon(pokemon, criticity=1):
    name = pokemonsJSON.get(str(pokemon['pokemonId']), 'Unknown')

    distances = []
    for item in LOCATIONS:
        for location, coordinates in item.items():
            distances.append('%i meters from %s' % (
                    int(lonlat_to_meters(coordinates[0], coordinates[1], pokemon['latitude'], pokemon['longitude'])),
                    location
                ))

    seconds = pokemon['expiration_time'] - time.time()

    if criticity == 1:
        message = 'New pokemon available: %s (%s) for %i:%i' % (name, ', '.join(distances), seconds // 60, seconds % 60)
    elif criticity == 2:
        message = 'You should consider going out for this one: %s (%s) for %i:%i' % (name, ', '.join(distances), seconds // 60, seconds % 60)
    elif criticity == 3:
        message = 'You know what? RUN AND GO GET THIS ONE: %s (%s) for %i:%i' % (name, ', '.join(distances), seconds // 60, seconds % 60)

    params = {
      'auth_token': HIPCHAT_API_KEY,
      'room_id': HIPCHAT_ROOM,
      'from': 'Pokevision',
      'color': 'purple',
      'notify': '1',
      'message_format': 'text',
      'message': message
    }
    #print params
    r = requests.get("https://api.hipchat.com/v1/rooms/message", params=params)



pokemons = get_latest_pokemons(LATITUDE, LONGITUDE)

nearest_pokemons = [pokemon for pokemon in pokemons if lonlat_to_meters(LATITUDE, LONGITUDE, pokemon['latitude'], pokemon['longitude']) <= MAX_DISTANCE]
go_out_pokemons = [pokemon for pokemon in pokemons if pokemon['id'] in WORTH_GOING_OUT]
stop_everything_pokemons = [pokemon for pokemon in pokemons if pokemon['id'] in STOP_EVERYTHING_YOURE_DOING]

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

for pokemon in stop_everything_pokemons:
    if (pokemon['latitude'], pokemon['longitude']) not in cache_coordinates:
    #if pokemon['id'] not in cache:
        print "New pokemon: %s" % json.dumps(pokemon)
        notif_hipchat_new_pokemon(pokemon, 3)

for pokemon in go_out_pokemons:
    if (pokemon['latitude'], pokemon['longitude']) not in cache_coordinates:
    #if pokemon['id'] not in cache:
        print "New pokemon: %s" % json.dumps(pokemon)
        notif_hipchat_new_pokemon(pokemon, 2)

for pokemon in nearest_pokemons:
    if (pokemon['latitude'], pokemon['longitude']) not in cache_coordinates:
    #if pokemon['id'] not in cache:
        if pokemon['pokemonId'] not in POKEMON_IDS_TO_FILTER:
            #print "New pokemon: %s" % json.dumps(pokemon)
            notif_hipchat_new_pokemon(pokemon)

# Write json cache
cache = nearest_pokemons
#cache = [pokemon['id'] for pokemon in nearest_pokemons]
with open(CACHE_FILE, 'w') as f:
    json.dump(cache, f)
    f.close()
