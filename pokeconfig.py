import os
import logging

logger = logging.getLogger(__name__)

class Pokeconfig:
    # constants
    WALK_MILES_PER_SECOND = 0.0008333 # assumes 3mph (or 0.0008333 miles per second) walking speed
    WALK_METERS_PER_SECOND = 1.34112 # conversion from 3mph
    EXPIRE_BUFFER_SECONDS = 5 # if a pokemon expires in 5 seconds or less (includes negative/stale pokemon), dont send it

    # configured via env
    auth_service = None
    username = None
    password = None
    location_name = None
    rarity_limit = 3
    slack_webhook_url = None
    num_steps = 5
    distance_unit = None
    position = ()

    def load_config(self, config_path):
        is_local = False
        if not 'DYNO' in os.environ:
            is_local = True
            if not os.path.exists(config_path):
                logging.error('please create a .env file in this directory in order to run locally!')
                exit(-1)

        # used for local testing without starting up heroku
        if is_local:
            env = {}
            logger.info('running locally, reading config from %s', config_path)
            with open(config_path, 'r') as fp:
                for line in fp:
                    idx = line.index('=')
                    key = line[:idx]
                    value = line[idx + 1:].strip()
                    env[key] = value
        else:
            logger.info('running on heroku, reading config from environment')
            env = os.environ

        try:
            self.auth_service = str(env['AUTH_SERVICE'])
            self.username = str(env['USERNAME'])
            self.password = str(env['PASSWORD'])
            self.location_name = str(env['LOCATION_NAME'])
            self.rarity_limit = int(env['RARITY_LIMIT'])
            self.slack_webhook_url = str(env['SLACK_WEBHOOK_URL'])
            self.num_steps = int(env['NUM_STEPS'])
            self.distance_unit = str(env['DISTANCE_UNIT'])
        except KeyError as ke:
            logging.error('key must be defined in config: %s!', ke)
            exit(-1)

        Pokeconfig._instance = self
        logger.info('loaded config with params')
        for config in ['auth_service', 'username', 'location_name', 'rarity_limit', 'slack_webhook_url', 'num_steps']:
            logger.info('%s=%s', config, getattr(self, config))

    _instance = None
    @staticmethod
    def get():
        return Pokeconfig._instance
