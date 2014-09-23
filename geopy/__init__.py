"""
geopy is a Python 2 and 3 client for several popular geocoding web services.

geopy makes it easy for Python developers to locate the coordinates of
addresses, cities, countries, and landmarks across the globe using third-party
geocoders and other data sources.
"""

from geopy.point import Point
from geopy.location import Location
from geopy.geocoders import * # pylint: disable=W0401


__version__ = "1.3.0"
