from geopy.point import Point
from geopy.location import Location
from geopy import geocoders

VERSION = (0, 95, 1)

def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    if VERSION[3:]:
        version = '%s.%s' % (version, VERSION[3])
    return version
