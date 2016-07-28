import calendar
import csv

from base64 import b64encode
from datetime import datetime
from geopy.distance import vincenty

from pokeconfig import Pokeconfig

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

class Pokemon:
    position = ()
    latitude = None
    longitude = None
    pokemon_id = 0
    encounter_id = None
    spawnpoint_id = None
    disappear_time = None
    from_lure = False
    pokestop_id = 0
    name = None
    rarity = 1
    key = None

    @staticmethod
    def from_pokemon(pokemon):
        p = Pokemon()
        p.encounter_id =  b64encode(str(pokemon['encounter_id']))
        p.spawnpoint_id = pokemon['spawnpoint_id']
        p.pokemon_id = pokemon['pokemon_data']['pokemon_id']
        p.position = (pokemon['latitude'], pokemon['longitude'], 0)
        p.disappear_time =  datetime.utcfromtimestamp(
            (pokemon['last_modified_timestamp_ms'] +
             pokemon['time_till_hidden_ms']) / 1000.0)
        p._get_pokedata()
        return p

    @staticmethod
    def from_pokestop(pokestop):
        p = Pokemon()
        p.position = (pokestop['latitude'], pokestop['longitude'], 0)
        p.pokemon_id = pokestop['active_pokemon_id']
        p.disappear_time = pokestop['lure_expiration']
        p.from_lure = True
        p.pokestop_id = pokestop['pokestop_id']
        p._get_pokedata()
        return p

    def _get_pokedata(self):
        pokedata = Pokedata.get(self.pokemon_id)
        self.name = pokedata['name']
        self.rarity = pokedata['rarity']
        self.key = self._get_key()

    def _get_key(self):
        if self.from_lure:
            key = '%s_%s' % (self.pokestop_id, self.pokemon_id)
        else:
            key = self.encounter_id
        return key

    def expires_in(self):
        return self.disappear_time - datetime.utcnow()

    def expires_in_str(self):
        min_remaining = int(self.expires_in().total_seconds() / 60)
        return '%s%ss' % ('%dm' % min_remaining if min_remaining > 0 else '', self.expires_in().seconds - 60 * min_remaining)

    def get_distance(self):
        position = Pokeconfig.get().position
        distance = vincenty(position, self.position)
        if Pokeconfig.get().distance_unit == 'meters':
            return distance.meters
        else:
            return distance.miles

    def get_distance_str(self):
        if Pokeconfig.get().distance_unit == 'meters':
            return '{:.0f} meters'.format(self.get_distance())    
        else:
            return '{:.3f} miles'.format(self.get_distance())

    def __str__(self):
        return '%s<id:%s, key:%s, rarity: %s, expires_in: %s, distance: %s>' % (self.name, self.pokemon_id, self.key, self.rarity, self.expires_in_str(), self.get_distance_str())

def parse_map(map_dict):
    pokemons = {}
    pokestops = {}

    cells = map_dict['responses']['GET_MAP_OBJECTS']['map_cells']
    for cell in cells:
        for p in cell.get('wild_pokemons', []):
            pokemon = Pokemon.from_pokemon(p)
            pokemons[pokemon.key] = pokemon

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
    if pokestops:
        for key in pokestops.keys():
            pokestop = pokestops[key]
            pokemon_id = pokestop['active_pokemon_id']
            if pokemon_id:
                pokemon = Pokemon.from_pokestop(pokestop)
                if pokemon.pokemon_id and not pokemon.key in pokemons:
                    pokemons[pokemon.key] = pokemon

    return pokemons

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
