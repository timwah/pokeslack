import logging

from geopy.geocoders import GoogleV3

logger = logging.getLogger(__name__)

def get_pos_by_name(location_name):
    geolocator = GoogleV3()
    loc = geolocator.geocode(location_name, timeout=10)

    logger.debug('location: %s', loc.address.encode('utf-8'))
    logger.debug('lat, long, alt: %s, %s, %s', loc.latitude, loc.longitude, loc.altitude)

    return (loc.latitude, loc.longitude, loc.altitude), loc.address.encode('utf-8')
