import json
import logging
import math
import random
import time

from datetime import datetime
from pgoapi.utilities import f2i
from s2sphere import CellId, LatLng

from pokedata import Pokedata, parse_map

logger = logging.getLogger(__name__)

REQ_SLEEP = 1
MAX_NUM_RETRIES = 10

#Constants for Hex Grid
#Gap between vertical and horzonal "rows"
lat_gap_meters = 150
lng_gap_meters = 86.6

#111111m is approx 1 degree Lat, which is close enough for this
meters_per_degree = 111111
lat_gap_degrees = float(lat_gap_meters) / meters_per_degree

def calculate_lng_degrees(lat):
    return float(lng_gap_meters) / (meters_per_degree * math.cos(math.radians(lat)))

class Pokesearch:
    def __init__(self, api, auth_service, username, password, position):
        self.api = api
        self.auth_service = auth_service
        self.username = username
        self.password = password
        self.position = position
        self.visible_range_meters = 70


    def login(self):
        logger.info('login start with service: %s', self.auth_service)

        self.api.set_position(*self.position)

        while not self.api.login(self.auth_service, self.username, self.password):
            logger.warn('failed to login to pokemon go, retrying...')
            time.sleep(REQ_SLEEP)

        self._update_download_settings()

        logger.info('login successful')

    def search(self, position, num_steps):
        if self.api._auth_provider and self.api._auth_provider._ticket_expire:
            if isinstance(self.api._auth_provider._ticket_expire, (int, long)):
                remaining_time = self.api._auth_provider._ticket_expire / 1000.0 - time.time()
                if remaining_time > 60:
                    logger.info("Skipping Pokemon Go login process since already logged in for another {:.2f} seconds".format(remaining_time))
                else:
                    self.login()
            else:
                logger.warn("skipping login since _ticket_expire was a token.")
        else:
            self.login()

        all_pokemon = {}
        num_retries = 0

        for step, coord in enumerate(generate_location_steps(position, num_steps, self.visible_range_meters), 1):
            lat = coord[0]
            lng = coord[1]
            self.api.set_position(*coord)

            cell_ids = get_cell_ids(lat, lng)
            timestamps = [0,] * len(cell_ids)

            response_dict = None
            while not response_dict:
                try:
                    self.api.get_map_objects(latitude = f2i(lat), longitude = f2i(lng), since_timestamp_ms = timestamps, cell_id = cell_ids)
                    response_dict = self.api.call()
                except:
                    logging.warn('exception happened on get_map_objects api call', exc_info=True)
                if not response_dict:
                    if num_retries < MAX_NUM_RETRIES:
                        num_retries += 1
                        logger.warn('get_map_objects failed, retrying in %s seconds, %s retries', REQ_SLEEP, num_retries)
                        time.sleep(REQ_SLEEP)
                    else:
                        logger.warn('MAX_NUM_RETRIES exceeded, retrying login...')
                        self.login()
                        raise StopIteration

            # try:
            pokemons = parse_map(response_dict)
            # except KeyError as e:
            #     logger.error('failed to parse map with key error: %s', e)

            for key in pokemons.keys():
                if not key in all_pokemon:
                    pokemon = pokemons[key]
                    all_pokemon[key] = pokemon
                    yield pokemon
                # else:
                #     logger.info("have duplicate poke: %s", key)
            total_steps = (3 * (num_steps**2)) - (3 * num_steps) + 1
            logger.info('Completed {:5.2f}% of scan.'.format(float(step) / total_steps * 100))
            time.sleep(REQ_SLEEP)

    def _update_download_settings(self):
        visible_range_meters = 0
        while visible_range_meters == 0:
            try:
                logger.info('fetching download settings...')
                self.api.download_settings(hash="05daf51635c82611d1aac95c0b051d3ec088a930")
                response_dict = self.api.call()
                visible_range_meters = response_dict['responses']['DOWNLOAD_SETTINGS']['settings']['map_settings']['pokemon_visible_range']
                self.visible_range_meters = float(visible_range_meters)
            except:
                logging.warn('exception happened on download_settings api call', exc_info=True)
        logger.info('download settings[pokemon_visible_range]: %s', self.visible_range_meters)

def generate_location_steps(position, num_steps, visible_range_meters):
    #Bearing (degrees)
    NORTH = 0
    EAST = 90
    SOUTH = 180
    WEST = 270

    pulse_radius = visible_range_meters / 1000.0 # km - radius of players heartbeat is 100m
    xdist = math.sqrt(3)*pulse_radius   # dist between column centers
    ydist = 3*(pulse_radius/2)          # dist between row centers

    yield (position[0], position[1], 0) #insert initial location

    ring = 1
    loc = position
    while ring < num_steps:
        #Set loc to start at top left
        loc = get_new_coords(loc, ydist, NORTH)
        loc = get_new_coords(loc, xdist/2, WEST)
        for direction in range(6):
            for i in range(ring):
                if direction == 0: # RIGHT
                    loc = get_new_coords(loc, xdist, EAST)
                if direction == 1: # DOWN + RIGHT
                    loc = get_new_coords(loc, ydist, SOUTH)
                    loc = get_new_coords(loc, xdist/2, EAST)
                if direction == 2: # DOWN + LEFT
                    loc = get_new_coords(loc, ydist, SOUTH)
                    loc = get_new_coords(loc, xdist/2, WEST)
                if direction == 3: # LEFT
                    loc = get_new_coords(loc, xdist, WEST)
                if direction == 4: # UP + LEFT
                    loc = get_new_coords(loc, ydist, NORTH)
                    loc = get_new_coords(loc, xdist/2, WEST)
                if direction == 5: # UP + RIGHT
                    loc = get_new_coords(loc, ydist, NORTH)
                    loc = get_new_coords(loc, xdist/2, EAST)
                yield (loc[0], loc[1], 0)
        ring += 1

def get_new_coords(init_loc, distance, bearing):
    """ Given an initial lat/lng, a distance(in kms), and a bearing (degrees),
    this will calculate the resulting lat/lng coordinates.
    """
    R = 6378.1 #km radius of the earth
    bearing = math.radians(bearing)

    init_coords = [math.radians(init_loc[0]), math.radians(init_loc[1])] # convert lat/lng to radians

    new_lat = math.asin( math.sin(init_coords[0])*math.cos(distance/R) +
        math.cos(init_coords[0])*math.sin(distance/R)*math.cos(bearing))

    new_lon = init_coords[1] + math.atan2(math.sin(bearing)*math.sin(distance/R)*math.cos(init_coords[0]),
        math.cos(distance/R)-math.sin(init_coords[0])*math.sin(new_lat))

    return [math.degrees(new_lat), math.degrees(new_lon)]

def get_cell_ids(lat, lng, radius = 10):
    origin = CellId.from_lat_lng(LatLng.from_degrees(lat, lng)).parent(15)
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
