import json
import logging
import random
import time

from datetime import datetime
from pgoapi.utilities import f2i
from s2sphere import CellId, LatLng

from pokedata import Pokedata, parse_map

logger = logging.getLogger(__name__)

REQ_SLEEP = 1
TIMESTAMP = '\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000'

class Pokesearch:
    def __init__(self, api, auth_service, username, password, position):
        self.api = api
        self.auth_service = auth_service
        self.username = username
        self.password = password
        self.position = position

    def login(self):
        logger.info('login start with service: %s', self.auth_service)

        self.api.set_position(*self.position)

        while not self.api.login(self.auth_service, self.username, self.password):
            logger.warn('failed to login to pokemon go, retrying...')
            time.sleep(REQ_SLEEP)

        logger.info('login successful')

    def search(self, lat, lng, step_limit, step_size):
        if self.api._auth_provider and self.api._auth_provider._ticket_expire:
            remaining_time = long(self.api._auth_provider._ticket_expire) / 1000.0 - time.time()
            if remaining_time > 60:
                logger.info("Skipping Pokemon Go login process since already logged in for another {:.2f} seconds".format(remaining_time))
            else:
                self.login()
        else:
            self.login()

        # coords = generate_spiral(lat, lng, step_size, step_limit)
        coords = generate_location_steps(lat, lng, step_size, step_limit)
        all_pokemon = {}
        i = 1
        for coord in coords:
            lat = coord['lat']
            lng = coord['lng']
            self.api.set_position(lat, lng, 0)

            cell_ids = get_cell_ids(lat, lng)
            timestamps = [0,] * len(cell_ids)

            self.api.get_map_objects(latitude = f2i(lat), longitude = f2i(lng), since_timestamp_ms = timestamps, cell_id = cell_ids)
            response_dict = self.api.call()

            while not response_dict:
                logger.info('Map Download failed. Trying again.')
                self.api.get_map_objects(latitude = f2i(lat), longitude = f2i(lng), since_timestamp_ms = timestamps, cell_id = cell_ids)
                response_dict = self.api.call()
                time.sleep(REQ_SLEEP)

            try:
                pokemons, pokestops, gyms = parse_map(response_dict)
            except KeyError as e:
                logger.error('failed to parse map with key error: %s', e)

            for key in pokemons.keys():
                if not key in all_pokemon:
                    pokemon = pokemons[key]
                    expires_in = pokemon['disappear_time'] - datetime.utcnow()
                    pokemon_id = pokemon['pokemon_id']
                    pokedata = Pokedata.get(pokemon_id)
                    pokemon['name'] = pokedata['name']
                    pokemon['rarity'] = pokedata['rarity']
                    pokemon['key'] = key
                    logger.info("adding pokemon: %s - %s, rarity: %s, expires in: %s", pokemon_id, pokemon['name'], pokemon['rarity'], expires_in)
                    all_pokemon[key] = pokemon
                # else:
                #     logger.info("have duplicate poke: %s", key)

            logger.info('Completed {:5.2f}% of scan.'.format(float(i) / step_limit**2*100))
            i += 1
            time.sleep(REQ_SLEEP)
        return all_pokemon

def generate_location_steps(starting_lat, startin_lng, step_size, step_limit):
    pos, x, y, dx, dy = 1, 0, 0, 0, -1
    while -step_limit / 2 < x <= step_limit / 2 and -step_limit / 2 < y <= step_limit / 2:
        yield {'lat': x * step_size + starting_lat, 'lng': y * step_size + startin_lng}
        if x == y or (x < 0 and x == -y) or (x > 0 and x == 1 - y):
            dx, dy = -dy, dx
        x, y = x + dx, y + dy

def generate_spiral(starting_lat, starting_lng, step_size, step_limit):
    yield {'lat': starting_lat, 'lng': starting_lng}
    steps,x,y,d,m = 1, 0, 0, 1, 1
    rlow = 0.0
    rhigh = 0.0005

    while steps < step_limit:
        while 2 * x * d < m and steps < step_limit:
            x = x + d
            steps += 1
            lat = x * step_size + starting_lat + random.uniform(rlow, rhigh)
            lng = y * step_size + starting_lng + random.uniform(rlow, rhigh)
            yield {'lat': lat, 'lng': lng}
        while 2 * y * d < m and steps < step_limit:
            y = y + d
            steps += 1
            lat = x * step_size + starting_lat + random.uniform(rlow, rhigh)
            lng = y * step_size + starting_lng + random.uniform(rlow, rhigh)
            yield {'lat': lat, 'lng': lng}

        d = -1 * d
        m = m + 1

def get_cell_ids(lat, long, radius = 10):
    origin = CellId.from_lat_lng(LatLng.from_degrees(lat, long)).parent(15)
    walk = [origin.id()]
    right = origin.next()
    left = origin.prev()

    # Search around provided radius
    for i in range(radius):
        walk.append(right.id())
        walk.append(left.id())
        right = right.next()
        left = left.prev()

    # Return everything
    return sorted(walk)
