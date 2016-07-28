import json
import logging
import os
import sys
import time

from datetime import datetime
from pgoapi import PGoApi

from pokeconfig import Pokeconfig
from pokedata import json_deserializer, json_serializer
from pokesearch import Pokesearch
from pokeslack import Pokeslack
from pokeutil import get_pos_by_name

logger = logging.getLogger(__name__)

if __name__ == '__main__':

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('pgoapi.pgoapi').setLevel(logging.WARNING)
    logging.getLogger('pgoapi.rpc_api').setLevel(logging.WARNING)

    logging.info('Pokeslack starting...')

    config = Pokeconfig()
    config.load_config('.env')

    auth_service = config.auth_service
    username = config.username
    password = config.password
    location_name = config.location_name
    rarity_limit = config.rarity_limit
    slack_webhook_url = config.slack_webhook_url
    num_steps = config.num_steps

    # debug vars, used to test slack integration w/o waiting
    use_cache = False
    cached_filename = 'cached_pokedata.json'
    search_timeout = 30

    position, address = get_pos_by_name(location_name)
    config.position = position
    logger.info('location_name: %s', address)

    api = PGoApi()
    pokesearch = Pokesearch(api, auth_service, username, password, position)
    pokeslack = Pokeslack(rarity_limit, slack_webhook_url)

    if not use_cache or not os.path.exists(cached_filename):
        logger.info('searching starting at latlng: (%s, %s)', position[0], position[1])
        pokesearch.login()
        while True:
            pokemons = []
            for pokemon in pokesearch.search(position, num_steps):
                logger.info('adding pokemon: %s', pokemon)
                pokeslack.try_send_pokemon(pokemon, debug=False)
                pokemons.append(pokemon)
            with open(cached_filename, 'w') as fp:
                json.dump(pokemons, fp, default=json_serializer, indent=4)
            logging.info('done searching, waiting %s seconds...', search_timeout)
            time.sleep(search_timeout)
    else:
        with open(cached_filename, 'r') as fp:
            pokemons = json.load(fp, object_hook=json_deserializer)
            # for pokemon in pokemons:
                # logger.info('loaded pokemon: %s', pokemon)
                # pokeslack.try_send_pokemon(pokemon, position, distance, debug=True)
        logger.info('loaded cached pokemon data for %s pokemon', len(pokemons))
