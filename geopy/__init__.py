"""
geopy is a Python 2 and 3 client for several popular geocoding web services.

geopy makes it easy for Python developers to locate the coordinates of
addresses, cities, countries, and landmarks across the globe using third-party
geocoders and other data sources.

geopy is tested against CPython (versions 2.7, 3.4, 3.5, 3.6, 3.7), PyPy, and
PyPy3. geopy does not and will not support CPython 2.6.
"""

from geopy.location import Location  # noqa
from geopy.point import Point  # noqa
from geopy.util import __version__  # noqa

from geopy.geocoders import *  # noqa
# geopy.geocoders.options must not be importable as `geopy.options`,
# because that is ambiguous (which options are that).
del options  # noqa
