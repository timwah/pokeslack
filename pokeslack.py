# -*- coding: UTF-8 -*-

import json
import logging
import requests

from datetime import datetime
from pokeconfig import Pokeconfig

logger = logging.getLogger(__name__)

class Pokeslack:
    def __init__(self, rarity_limit, slack_webhook_url):
        self.sent_pokemon = {}
        self.rarity_limit = rarity_limit
        self.slack_webhook_url = slack_webhook_url

    def try_send_pokemon(self, pokemon, debug):

        if pokemon.expires_in().total_seconds() < Pokeconfig.EXPIRE_BUFFER_SECONDS:
            logger.info('skipping pokemon since it expires too soon')
            return

        if pokemon.rarity < self.rarity_limit:
            logger.info('skipping pokemon since its rarity is too low')
            return

        padded_distance = pokemon.get_distance() * 1.1
        walk_distance_per_second = Pokeconfig.WALK_METERS_PER_SECOND if Pokeconfig.get().distance_unit == 'meters' else Pokeconfig.WALK_MILES_PER_SECOND
        travel_time = padded_distance / walk_distance_per_second
        if pokemon.expires_in().total_seconds() < travel_time:
            logger.info('skipping pokemon since it\'s too far: traveltime=%s for distance=%s', travel_time, pokemon.get_distance_str())
            return

        pokemon_key = pokemon.key
        if pokemon_key in self.sent_pokemon:
            logger.info('already sent this pokemon to slack with key %s', pokemon_key)
            return

        from_lure = ', from a lure' if pokemon.from_lure else ''
        miles_away = pokemon.get_distance_str()

        position = Pokeconfig.get().position

        pokedex_url = 'http://www.pokemon.com/us/pokedex/%s' % pokemon.pokemon_id
        map_url = 'http://maps.google.com?saddr=%s,%s&daddr=%s,%s&directionsmode=walking' % (position[0], position[1], pokemon.position[0], pokemon.position[1])
        time_remaining = pokemon.expires_in_str()
        stars = ''.join([':star:' for x in xrange(pokemon.rarity)])
        message = 'I found a <%s|%s> %s <%s|%s away> expiring in %s%s' % (pokedex_url, pokemon.name, stars, map_url, miles_away, time_remaining, from_lure)
        # bold message if rarity > 4
        if pokemon.rarity >= 4:
            message = '*%s*' % message

        logging.info('%s: %s', pokemon_key, message)
        if self._send(message):
            self.sent_pokemon[pokemon_key] = True

    def _send(self, message):
        payload = {
            'username': 'Poké Alert!',
            'text': message,
            'icon_emoji': ':ghost:'
        }
        s = json.dumps(payload)
        r = requests.post(self.slack_webhook_url, data=s)
        logger.info('slack post result: %s, %s', r.status_code, r.reason)
        return r.status_code == 200
