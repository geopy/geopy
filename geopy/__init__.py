import logging
from geopy.point import Point
from geopy.location import Location
from geopy import geocoders

logging.basicConfig(
    format="[%(name)s:%(levelname)s] %(message)s",
    level=logging.DEBUG
)
