"""
Each geolocation service you might use, such as Google Maps, Bing Maps, or
Nominatim, has its own class in ``geopy.geocoders`` abstracting the service's
API. Geocoders each define at least a ``geocode`` method, for resolving a
location from a string, and may define a ``reverse`` method, which resolves a
pair of coordinates to an address. Each Geocoder accepts any credentials
or settings needed to interact with its service, e.g., an API key or
locale, during its initialization.

To geolocate a query to an address and coordinates:

    >>> from geopy.geocoders import Nominatim
    >>> geolocator = Nominatim(user_agent="specify_your_app_name_here")
    >>> location = geolocator.geocode("175 5th Avenue NYC")
    >>> print(location.address)
    Flatiron Building, 175, 5th Avenue, Flatiron, New York, NYC, New York, ...
    >>> print((location.latitude, location.longitude))
    (40.7410861, -73.9896297241625)
    >>> print(location.raw)
    {'place_id': '9167009604', 'type': 'attraction', ...}


To find the address corresponding to a set of coordinates:

    >>> from geopy.geocoders import Nominatim
    >>> geolocator = Nominatim(user_agent="specify_your_app_name_here")
    >>> location = geolocator.reverse("52.509669, 13.376294")
    >>> print(location.address)
    Potsdamer Platz, Mitte, Berlin, 10117, Deutschland, European Union
    >>> print((location.latitude, location.longitude))
    (52.5094982, 13.3765983)
    >>> print(location.raw)
    {'place_id': '654513', 'osm_type': 'node', ...}

Locators' ``geocode`` and ``reverse`` methods require the argument ``query``,
and also accept at least the argument ``exactly_one``, which is ``True`` by
default.
Geocoders may have additional attributes, e.g., Bing accepts ``user_location``,
the effect of which is to bias results near that location. ``geocode``
and ``reverse`` methods  may return three types of values:

- When there are no results found, returns ``None``.

- When the method's ``exactly_one`` argument is ``True`` and at least one
  result is found, returns a :class:`geopy.location.Location` object, which
  can be iterated over as:

    ``(address<String>, (latitude<Float>, longitude<Float>))``

  Or can be accessed as ``location.address``, ``location.latitude``,
  ``location.longitude``, ``location.altitude``, and ``location.raw``. The
  last contains the full geocoder's response for this result.

- When ``exactly_one`` is ``False``, and there is at least one result, returns a
  list of :class:`geopy.location.Location` objects, as above:

    ``[location, [...]]``

If a service is unavailable or otherwise returns a non-OK response, or doesn't
receive a response in the allotted timeout, you will receive one of the
`Exceptions`_ detailed below.

.. _specifying_parameters_once:

Specifying Parameters Once
~~~~~~~~~~~~~~~~~~~~~~~~~~

Geocoding methods accept a lot of different parameters, and you would
probably want to specify some of them just once and not care about them
later.

This is easy to achieve with Python's :func:`functools.partial`::

    >>> from functools import partial
    >>> from geopy.geocoders import Nominatim

    >>> geolocator = Nominatim(user_agent="specify_your_app_name_here")

    >>> geocode = partial(geolocator.geocode, language="es")
    >>> print(geocode("london"))
    Londres, Greater London, Inglaterra, SW1A 2DX, Gran Bretaña
    >>> print(geocode("paris"))
    París, Isla de Francia, Francia metropolitana, Francia
    >>> print(geocode("paris", language="en"))
    Paris, Ile-de-France, Metropolitan France, France

    >>> reverse = partial(geolocator.reverse, language="es")
    >>> print(reverse("52.509669, 13.376294"))
    Steinecke, Potsdamer Platz, Tiergarten, Mitte, 10785, Alemania

If you need to modify the query, you can also use a one-liner with lambda.
For example, if you only need to geocode locations in `Cleveland, Ohio`,
you could do::

    >>> geocode = lambda query: geolocator.geocode("%s, Cleveland OH" % query)
    >>> print(geocode("11111 Euclid Ave"))
    Thwing Center, Euclid Avenue, Magnolia-Wade Park Historic District,
    University Circle, Cleveland, Cuyahoga County, Ohio, 44106, United States
    of America

That lambda doesn't accept kwargs. If you need them, you could do::

    >>> _geocode = partial(geolocator.geocode, language="es")
    >>> geocode = lambda query, **kw: _geocode("%s, Cleveland OH" % query, **kw)
    >>> print(geocode("11111 Euclid Ave"))
    Thwing Center, Euclid Avenue, Magnolia-Wade Park Historic District,
    University Circle, Cleveland, Cuyahoga County, Ohio, 44106, Estados Unidos
    >>> print(geocode("11111 Euclid Ave", language="en"))
    Thwing Center, Euclid Avenue, Magnolia-Wade Park Historic District,
    University Circle, Cleveland, Cuyahoga County, Ohio, 44106, United States
    of America

Geopy Is Not a Service
~~~~~~~~~~~~~~~~~~~~~~

Geocoding is provided by a number of different services, which are not
affiliated with geopy in any way. These services provide APIs, which anyone
could implement, and geopy is just a library which provides these
implementations for many different services in a single package.

.. image:: ./_static/geopy_and_geocoding_services.svg
   :target: ./_static/geopy_and_geocoding_services.svg

Therefore:

1. Different services have different Terms of Use, quotas, pricing,
   geodatabases and so on. For example, :class:`.Nominatim`
   is free, but provides low request limits. If you need to make more queries,
   consider using another (probably paid) service, such as
   :class:`.OpenMapQuest` or :class:`.PickPoint`
   (these two are commercial providers of Nominatim, so they should
   have the same data and APIs). Or, if you are ready to wait, you can try
   :mod:`geopy.extra.rate_limiter`.

2. geopy cannot be responsible for the geocoding services' databases.
   If you have issues with some queries which the service cannot fulfill,
   it should be directed to that service's support team.

3. geopy cannot be responsible for any networking issues between your computer
   and the geocoding service.

If you face any problem with your current geocoding service provider, you can
always try a different one.

.. _async_mode:

Async Mode
~~~~~~~~~~

By default geopy geocoders are synchronous (i.e. they use an Adapter
based on :class:`.BaseSyncAdapter`).

All geocoders can be used with asyncio by simply switching to an
Adapter based on :class:`.BaseAsyncAdapter` (like :class:`.AioHTTPAdapter`).

Example::

    from geopy.adapters import AioHTTPAdapter
    from geopy.geocoders import Nominatim

    async with Nominatim(
        user_agent="specify_your_app_name_here",
        adapter_factory=AioHTTPAdapter,
    ) as geolocator:
        location = await geolocator.geocode("175 5th Avenue NYC")
        print(location.address)

Basically the usage is the same as in synchronous mode, except that
all geocoder calls should be used with ``await``, and the geocoder
instance should be created by ``async with``. The context manager is optional,
however, it is strongly advised to use it to avoid resources leaks.

"""

__all__ = (
    "get_geocoder_for_service",
    "options",
    # The order of classes below should correspond to the order of their
    # files in the ``geocoders`` directory ordered by name.
    #
    # If you're adding a new geocoder class, then you should mention it in
    # this module 3 times:
    # 1. In this ``__all__`` tuple.
    # 2. In the imports block below.
    # 3. In the ``SERVICE_TO_GEOCODER`` dict below.
    #
    # Also don't forget to pull up the list of geocoders
    # in the docs: docs/index.rst
    "AlgoliaPlaces",
    "ArcGIS",
    "AzureMaps",
    "Baidu",
    "BaiduV3",
    "BANFrance",
    "Bing",
    "DataBC",
    "GeocodeEarth",
    "Geocodio",
    "GeoNames",
    "GoogleV3",
    "Geolake",
    "Here",
    "HereV7",
    "IGNFrance",
    "MapBox",
    "MapQuest",
    "MapTiler",
    "Nominatim",
    "OpenCage",
    "OpenMapQuest",
    "PickPoint",
    "Pelias",
    "Photon",
    "LiveAddress",
    "TomTom",
    "What3Words",
    "What3WordsV3",
    "Yandex",
)


from geopy.exc import GeocoderNotFound
from geopy.geocoders.algolia import AlgoliaPlaces
from geopy.geocoders.arcgis import ArcGIS
from geopy.geocoders.azure import AzureMaps
from geopy.geocoders.baidu import Baidu, BaiduV3
from geopy.geocoders.banfrance import BANFrance
from geopy.geocoders.base import options
from geopy.geocoders.bing import Bing
from geopy.geocoders.databc import DataBC
from geopy.geocoders.geocodeearth import GeocodeEarth
from geopy.geocoders.geocodio import Geocodio
from geopy.geocoders.geolake import Geolake
from geopy.geocoders.geonames import GeoNames
from geopy.geocoders.google import GoogleV3
from geopy.geocoders.here import Here, HereV7
from geopy.geocoders.ignfrance import IGNFrance
from geopy.geocoders.mapbox import MapBox
from geopy.geocoders.mapquest import MapQuest
from geopy.geocoders.maptiler import MapTiler
from geopy.geocoders.nominatim import Nominatim
from geopy.geocoders.opencage import OpenCage
from geopy.geocoders.openmapquest import OpenMapQuest
from geopy.geocoders.pelias import Pelias
from geopy.geocoders.photon import Photon
from geopy.geocoders.pickpoint import PickPoint
from geopy.geocoders.smartystreets import LiveAddress
from geopy.geocoders.tomtom import TomTom
from geopy.geocoders.what3words import What3Words, What3WordsV3
from geopy.geocoders.yandex import Yandex

SERVICE_TO_GEOCODER = {
    "algolia": AlgoliaPlaces,
    "arcgis": ArcGIS,
    "azure": AzureMaps,
    "baidu": Baidu,
    "baiduv3": BaiduV3,
    "banfrance": BANFrance,
    "bing": Bing,
    "databc": DataBC,
    "geocodeearth": GeocodeEarth,
    "geocodio": Geocodio,
    "geonames": GeoNames,
    "google": GoogleV3,
    "googlev3": GoogleV3,
    "geolake": Geolake,
    "here": Here,
    "herev7": HereV7,
    "ignfrance": IGNFrance,
    "mapbox": MapBox,
    "mapquest": MapQuest,
    "maptiler": MapTiler,
    "nominatim": Nominatim,
    "opencage": OpenCage,
    "openmapquest": OpenMapQuest,
    "pickpoint": PickPoint,
    "pelias": Pelias,
    "photon": Photon,
    "liveaddress": LiveAddress,
    "tomtom": TomTom,
    "what3words": What3Words,
    "what3wordsv3": What3WordsV3,
    "yandex": Yandex,
}


def get_geocoder_for_service(service):
    """
    For the service provided, try to return a geocoder class.

    >>> from geopy.geocoders import get_geocoder_for_service
    >>> get_geocoder_for_service("nominatim")
    geopy.geocoders.nominatim.Nominatim

    If the string given is not recognized, a
    :class:`geopy.exc.GeocoderNotFound` exception is raised.

    Given that almost all of the geocoders provide the ``geocode``
    method it could be used to make basic queries based entirely
    on user input::

        from geopy.geocoders import get_geocoder_for_service

        def geocode(geocoder, config, query):
            cls = get_geocoder_for_service(geocoder)
            geolocator = cls(**config)
            location = geolocator.geocode(query)
            return location.address

        >>> geocode("nominatim", dict(user_agent="specify_your_app_name_here"), \
"london")
        'London, Greater London, England, SW1A 2DX, United Kingdom'
        >>> geocode("photon", dict(), "london")
        'London, SW1A 2DX, London, England, United Kingdom'

    """
    try:
        return SERVICE_TO_GEOCODER[service.lower()]
    except KeyError:
        raise GeocoderNotFound(
            "Unknown geocoder '%s'; options are: %s" %
            (service, SERVICE_TO_GEOCODER.keys())
        )
