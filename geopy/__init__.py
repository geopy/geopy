"""
geopy is a Python client for several popular geocoding web services.

geopy makes it easy for Python developers to locate the coordinates of
addresses, cities, countries, and landmarks across the globe using
third-party geocoders and other data sources.

To geolocate a query to an address and coordinates::

    from geopy.geocoders import GoogleV3

    geolocator = GoogleV3()
    address, (latitude, longitude) = geolocator.geocode("175 5th Avenue NYC")
    print address, latitude, longitude
    # 175 5th Avenue, New York, NY 10010, USA 40.7410262 -73.9897806

To find the address corresponding to a set of coordinates::

    from geopy.geocoders import GoogleV3

    geolocator = GoogleV3()
    address, (latitude, longitude) = geolocator.reverse("40.752067, -73.977578", exactly_one=True)
    print address, latitude, longitude
    # 77 East 42nd Street, New York, NY 10017, USA 40.7520802 -73.9775683


Locators' ``geolocate`` and ``reverse`` methods may return three
types of values:

- When there are no results found, returns ``None``.

- When the method's ``exactly_one`` argument is ``True`` and at least one result is found, returns a tuple of:
    (address<String>, (latitude<Float>, longitude<Float>))

- When ``exactly_one`` is False, and there is at least one result, returns a list of tuples:
    [(address<String>, (latitude<Float>, longitude<Float>)), [...]]
"""

from geopy.point import Point
from geopy.location import Location
from geopy.geocoders import * # pylint: disable=W0401
