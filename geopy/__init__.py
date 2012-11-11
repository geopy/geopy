from geopy.point import Point
from geopy.location import Location
from geopy import geocoders

def get_version():
    import os
    f = os.path.join(os.path.dirname(__file__), 'version.txt')
    return open(f).read().strip()
