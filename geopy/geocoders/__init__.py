"""
Each geolocation service you might use, such as Google Maps, Bing Maps, or
Yahoo BOSS, has its own class in ``geopy.geocoders`` abstracting the service's
API. Geocoders each define at least a ``geocode`` method, for resolving a
location from a string, and may define a ``reverse`` method, which resolves a
pair of coordinates to an address. Each Geocoder accepts any credentials
or settings needed to interact with its service, e.g., an API key or
locale, during its initialization.

To geolocate a query to an address and coordinates::

    >>> from geopy.geocoders import GoogleV3
    >>> geolocator = GoogleV3()
    >>> address, (latitude, longitude) = geolocator.geocode("175 5th Avenue NYC")
    >>> print address, latitude, longitude
    175 5th Avenue, New York, NY 10010, USA 40.7410262 -73.9897806

To find the address corresponding to a set of coordinates::

    >>> from geopy.geocoders import GoogleV3
    >>> geolocator = GoogleV3()
    >>> address, (latitude, longitude) = geolocator.reverse("40.752067, -73.977578")
    >>> print address, latitude, longitude
    77 East 42nd Street, New York, NY 10017, USA 40.7520802 -73.9775683

Locators' ``geolocate`` and ``reverse`` methods require the argument ``query``,
and also accept at least the argument ``exactly_one``, which is ``True``.
Geocoders may have additional attributes, e.g., Bing accepts ``user_location``,
the effect of which is to bias results near that location. ``geolocate``
and ``reverse`` methods  may return three types of values:

- When there are no results found, returns ``None``.

- When the method's ``exactly_one`` argument is ``True`` and at least one result is found, returns a tuple of:
    (address<String>, (latitude<Float>, longitude<Float>))

- When ``exactly_one`` is False, and there is at least one result, returns a list of tuples:
    [(address<String>, (latitude<Float>, longitude<Float>)), [...]]

If a service is unavailable or otherwise returns a non-OK response you will
receive a :class:`.geopy.exc.GeocoderServiceError`.

Every geocoder accepts an argument ``format_string`` that defaults to '%s' where
the input string to geocode is interpolated. For example, if you only need to
geocode locations in Cleveland, Ohio, you could do::

    >>> from geopy.geocoders import GeocoderDotUS
    >>> geolocator = GeocoderDotUS(format_string="%s, Cleveland OH")
    >>> address, (latitude, longitude) = geolocator.geocode("11111 Euclid Ave")
    >>> print address, latitude, longitude
    11111 Euclid Ave, Cleveland, OH 44106 41.506784 -81.608148

"""

from geopy.geocoders.bing import Bing
from geopy.geocoders.googlev3 import GoogleV3
from geopy.geocoders.dot_us import GeocoderDotUS
from geopy.geocoders.geonames import GeoNames
from geopy.geocoders.wiki_gis import MediaWiki
from geopy.geocoders.wiki_semantic import SemanticMediaWiki
from geopy.geocoders.placefinder import YahooPlaceFinder
from geopy.geocoders.openmapquest import OpenMapQuest
from geopy.geocoders.mapquest import MapQuest
from geopy.geocoders.osm import Nominatim
