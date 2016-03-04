# geopy

[![Build Status](https://travis-ci.org/geopy/geopy.svg?branch=master)](https://travis-ci.org/geopy/geopy)

geopy is a Python 2 and 3 client for several popular geocoding web services.

geopy makes it easy for Python developers to locate the coordinates of
addresses, cities, countries, and landmarks across the globe using third-party
geocoders and other data sources.

geopy includes geocoder classes for the [OpenStreetMap Nominatim][osm],
[ESRI ArcGIS][arcgis], [Google Geocoding API (V3)][googlev3],
[Baidu Maps][baidu], [Bing Maps API][bing], [Yahoo! PlaceFinder][placefinder],
[Yandex][yandex], [IGN France][ignfrance], [GeoNames][geonames],
[NaviData][navidata], [OpenMapQuest][openmapquest], [What3Words][what3words],
[OpenCage][opencage], [SmartyStreets][smartystreets], [geocoder.us][dot_us],
[GeocodeFarm][geocodefarm], and NYC's [Geoclient][geoclient] geocoder services.
The various geocoder classes are located in [geopy.geocoders][geocoders_src].

[arcgis]: http://resources.arcgis.com/en/help/arcgis-rest-api/
[baidu]: http://developer.baidu.com/map/webservice-geocoding.htm
[bing]: http://www.microsoft.com/maps/developers/web.aspx
[dot_us]: http://geocoder.us/
[geoclient]: https://developer.cityofnewyork.us/api/geoclient-api
[geocodefarm]: https://www.geocodefarm.com/
[geonames]: http://www.geonames.org/
[googlev3]: https://developers.google.com/maps/documentation/geocoding/
[ignfrance]: http://api.ign.fr/tech-docs-js/fr/developpeur/search.html
[mapquest]: http://www.mapquestapi.com/geocoding/
[navidata]: http://navidata.pl
[opencage]: http://geocoder.opencagedata.com/api.html
[openmapquest]: http://developer.mapquest.com/web/products/open/geocoding-service
[osm]: https://wiki.openstreetmap.org/wiki/Nominatim
[placefinder]: https://developer.yahoo.com/boss/geo/docs/
[smartystreets]: https://smartystreets.com/products/liveaddress-api
[what3words]: http://what3words.com/api/reference
[yandex]: http://api.yandex.com/maps/doc/intro/concepts/intro.xml
[geocoders_src]: https://github.com/geopy/geopy/tree/master/geopy/geocoders

geopy is tested against CPython 2.7, CPython 3.2, CPython 3.4, PyPy, and
PyPy3. geopy does not and will not support CPython 2.6.

© geopy contributors 2006-2015 (see AUTHORS) under the
[MIT License](https://github.com/geopy/geopy/blob/master/LICENSE).

## Installation

Install using [pip](http://www.pip-installer.org/en/latest/) with:

    pip install geopy

Or, [download a wheel or source archive from PyPI](https://pypi.python.org/pypi/geopy).

## Geocoding

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


## Measuring Distance

Geopy can calculate geodesic distance between two points using the
[Vincenty distance](https://en.wikipedia.org/wiki/Vincenty\'s_formulae) or
[great-circle distance](https://en.wikipedia.org/wiki/Great-circle_distance)
formulas, with a default of Vincenty available as the class
`geopy.distance.distance`, and the computed distance available as attributes
(e.g., `miles`, `meters`, etc.).

Here's an example usage of Vincenty distance:

    >>> from geopy.distance import vincenty
    >>> newport_ri = (41.49008, -71.312796)
    >>> cleveland_oh = (41.499498, -81.695391)
    >>> print(vincenty(newport_ri, cleveland_oh).miles)
    538.3904451566326

Using great-circle distance:

    >>> from geopy.distance import great_circle
    >>> newport_ri = (41.49008, -71.312796)
    >>> cleveland_oh = (41.499498, -81.695391)
    >>> print(great_circle(newport_ri, cleveland_oh).miles)
    537.1485284062816

## Documentation

More documentation and examples can be found at
[Read the Docs](http://geopy.readthedocs.org/en/latest/).
