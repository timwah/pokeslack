import calendar
import csv

from base64 import b64encode
from datetime import datetime

class Pokedata:
    pokedata = None
    @staticmethod
    def get(pokemon_id):
        if not Pokedata.pokedata:
            Pokedata.pokedata = {}
            with open('pokedata.csv', 'rU') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    id = int(row[0])
                    name = row[1]
                    rarity = int(row[2])
                    Pokedata.pokedata[id] = {
                        'name': name,
                        'rarity': rarity
                    }
        return Pokedata.pokedata[pokemon_id]

def parse_map(map_dict):
    pokemons = {}
    pokestops = {}
    gyms = {}

    cells = map_dict['responses']['GET_MAP_OBJECTS']['map_cells']
    for cell in cells:
        for p in cell.get('wild_pokemons', []):
            pokemons[p['encounter_id']] = {
                'encounter_id': b64encode(str(p['encounter_id'])),
                'spawnpoint_id': p['spawnpoint_id'],
                'pokemon_id': p['pokemon_data']['pokemon_id'],
                'latitude': p['latitude'],
                'longitude': p['longitude'],
                'disappear_time': datetime.utcfromtimestamp(
                    (p['last_modified_timestamp_ms'] +
                     p['time_till_hidden_ms']) / 1000.0)
            }

        for f in cell.get('forts', []):
            if f.get('type') == 1:  # Pokestops
                if 'lure_info' in f:
                    lure_expiration = datetime.utcfromtimestamp(
                        f['lure_info']['lure_expires_timestamp_ms'] / 1000.0)
                    active_pokemon_id = f['lure_info']['active_pokemon_id']
                    # logger.debug("at fort: %s, have active pokemon_id: %s", f['lure_info']['fort_id'], active_pokemon_id)
                else:
                    lure_expiration, active_pokemon_id = None, None

                pokestops[f['id']] = {
                    'pokestop_id': f['id'],
                    'enabled': f['enabled'],
                    'latitude': f['latitude'],
                    'longitude': f['longitude'],
                    'last_modified': datetime.utcfromtimestamp(
                        f['last_modified_timestamp_ms'] / 1000.0),
                    'lure_expiration': lure_expiration,
                    'active_pokemon_id': active_pokemon_id
                }

            else:  # Currently, there are only stops and gyms
                gyms[f['id']] = {
                    'gym_id': f['id'],
                    'team_id': f.get('owned_by_team', 0),
                    'guard_pokemon_id': f.get('guard_pokemon_id', 0),
                    'gym_points': f.get('gym_points', 0),
                    'enabled': f['enabled'],
                    'latitude': f['latitude'],
                    'longitude': f['longitude'],
                    'last_modified': datetime.utcfromtimestamp(
                        f['last_modified_timestamp_ms'] / 1000.0),
                }

    if pokestops:
        for key in pokestops.keys():
            pokestop = pokestops[key]
            pokemon_id = pokestop['active_pokemon_id']
            if pokemon_id:
                key = '%s_%s' % (pokestop['pokestop_id'], pokemon_id)
                if not key in pokemons:
                    expires_in = pokestop['lure_expiration'] - datetime.utcnow()
                    pokemons[key] = {
                        'latitude': pokestop['latitude'],
                        'longitude': pokestop['longitude'],
                        'pokemon_id': pokemon_id,
                        'disappear_time': pokestop['lure_expiration'],
                        'from_lure': True
                    }
                # else:
                #     logger.info("dupe pokemon from stop detected for key: %s", key)

    return pokemons, pokestops, gyms

def json_deserializer(obj):
    for key, value in obj.items():
        if key == 'disappear_time':
            value = datetime.utcfromtimestamp(value / 1000.0)
            obj[key] = value
    return obj

def json_serializer(obj):
    try:
        if isinstance(obj, datetime):
            if obj.utcoffset() is not None:
                obj = obj - obj.utcoffset()
            millis = int(
                calendar.timegm(obj.timetuple()) * 1000 +
                obj.microsecond / 1000
            )
            return millis
        iterable = iter(obj)
    except TypeError:
        pass
    else:
        return list(iterable)
