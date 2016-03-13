"""
Each geolocation service you might use, such as Google Maps, Bing Maps, or
Yahoo BOSS, has its own class in ``geopy.geocoders`` abstracting the service's
API. Geocoders each define at least a ``geocode`` method, for resolving a
location from a string, and may define a ``reverse`` method, which resolves a
pair of coordinates to an address. Each Geocoder accepts any credentials
or settings needed to interact with its service, e.g., an API key or
locale, during its initialization.

To geolocate a query to an address and coordinates:

    >>> from geopy.geocoders import Nominatim
    >>> geolocator = Nominatim()
    >>> location = geolocator.geocode("175 5th Avenue NYC")
    >>> print(location.address)
    Flatiron Building, 175, 5th Avenue, Flatiron, New York, NYC, New York, ...
    >>> print((location.latitude, location.longitude))
    (40.7410861, -73.9896297241625)
    >>> print(location.raw)
    {'place_id': '9167009604', 'type': 'attraction', ...}


To find the address corresponding to a set of coordinates:

    >>> from geopy.geocoders import Nominatim
    >>> geolocator = Nominatim()
    >>> location = geolocator.reverse("52.509669, 13.376294")
    >>> print(location.address)
    Potsdamer Platz, Mitte, Berlin, 10117, Deutschland, European Union
    >>> print((location.latitude, location.longitude))
    (52.5094982, 13.3765983)
    >>> print(location.raw)
    {'place_id': '654513', 'osm_type': 'node', ...}

Locators' ``geolocate`` and ``reverse`` methods require the argument ``query``,
and also accept at least the argument ``exactly_one``, which is ``True``.
Geocoders may have additional attributes, e.g., Bing accepts ``user_location``,
the effect of which is to bias results near that location. ``geolocate``
and ``reverse`` methods  may return three types of values:

- When there are no results found, returns ``None``.

- When the method's ``exactly_one`` argument is ``True`` and at least one
  result is found, returns a :class:`geopy.location.Location` object, which
  can be iterated over as:

    (address<String>, (latitude<Float>, longitude<Float>))

  Or can be accessed as `Location.address`, `Location.latitude`,
  `Location.longitude`, `Location.altitude`, and `Location.raw`. The
  last contains the geocoder's unparsed response for this result.

- When ``exactly_one`` is False, and there is at least one result, returns a
  list of :class:`geopy.location.Location` objects, as above:

    [Location, [...]]

If a service is unavailable or otherwise returns a non-OK response, or doesn't
receive a response in the allotted timeout, you will receive one of the
`Exceptions`_ detailed below.

Every geocoder accepts an argument ``format_string`` that defaults to '%s'
where the input string to geocode is interpolated. For example, if you only
need to geocode locations in Cleveland, Ohio, you could do::

    >>> from geopy.geocoders import GeocoderDotUS
    >>> geolocator = GeocoderDotUS(format_string="%s, Cleveland OH")
    >>> address, (latitude, longitude) = geolocator.geocode("11111 Euclid Ave")
    >>> print(address, latitude, longitude)
    11111 Euclid Ave, Cleveland, OH 44106 41.506784 -81.608148

"""

__all__ = (
    "get_geocoder_for_service",
    "ArcGIS",
    "Baidu",
    "Bing",
    "DataBC",
    "GeocoderDotUS",
    "GeocodeFarm",
    "GeoNames",
    "GoogleV3",
    "IGNFrance",
    "OpenCage",
    "OpenMapQuest",
    "NaviData",
    "Nominatim",
    "YahooPlaceFinder",
    "LiveAddress",
    'Yandex',
    "What3Words",
    "Photon",
    "Mapzen",
)


from geopy.geocoders.arcgis import ArcGIS
from geopy.geocoders.baidu import Baidu
from geopy.geocoders.bing import Bing
from geopy.geocoders.databc import DataBC
from geopy.geocoders.dot_us import GeocoderDotUS
from geopy.geocoders.geocodefarm import GeocodeFarm
from geopy.geocoders.geonames import GeoNames
from geopy.geocoders.googlev3 import GoogleV3
from geopy.geocoders.opencage import OpenCage
from geopy.geocoders.openmapquest import OpenMapQuest
from geopy.geocoders.navidata import NaviData
from geopy.geocoders.osm import Nominatim
from geopy.geocoders.placefinder import YahooPlaceFinder
from geopy.geocoders.smartystreets import LiveAddress
from geopy.geocoders.what3words import What3Words
from geopy.geocoders.yandex import Yandex
from geopy.geocoders.ignfrance import IGNFrance
from geopy.geocoders.photon import Photon
from geopy.geocoders.mapzen import Mapzen


from geopy.exc import GeocoderNotFound


SERVICE_TO_GEOCODER = {
    "arcgis": ArcGIS,
    "baidu": Baidu,
    "bing": Bing,
    "databc": DataBC,
    "google": GoogleV3,
    "googlev3": GoogleV3,
    "geocoderdotus": GeocoderDotUS,
    "geonames": GeoNames,
    "yahoo": YahooPlaceFinder,
    "placefinder": YahooPlaceFinder,
    "opencage": OpenCage,
    "openmapquest": OpenMapQuest,
    "liveaddress": LiveAddress,
    "navidata": NaviData,
    "nominatim": Nominatim,
    "geocodefarm": GeocodeFarm,
    "what3words": What3Words,
    "yandex": Yandex,
    "ignfrance": IGNFrance,
    "photon": Photon
}


def get_geocoder_for_service(service):
    """
    For the service provided, try to return a geocoder class.

    >>> from geopy.geocoders import get_geocoder_for_service
    >>> get_geocoder_for_service("nominatim")
    geopy.geocoders.osm.Nominatim

    If the string given is not recognized, a
    :class:`geopy.exc.GeocoderNotFound` exception is raised.

    """
    try:
        return SERVICE_TO_GEOCODER[service.lower()]
    except KeyError:
        raise GeocoderNotFound(
            "Unknown geocoder '%s'; options are: %s" %
            (service, SERVICE_TO_GEOCODER.keys())
        )

