geopy
=====

.. image:: https://img.shields.io/pypi/v/geopy.svg?style=flat-square
    :target: https://pypi.python.org/pypi/geopy/
    :alt: Latest Version

.. image:: https://img.shields.io/travis/geopy/geopy.svg?style=flat-square
    :target: https://travis-ci.org/geopy/geopy
    :alt: Build Status

.. image:: https://img.shields.io/github/license/geopy/geopy.svg?style=flat-square
    :target: https://pypi.python.org/pypi/geopy/
    :alt: License


geopy is a Python 2 and 3 client for several popular geocoding web
services.

geopy makes it easy for Python developers to locate the coordinates of
addresses, cities, countries, and landmarks across the globe using
third-party geocoders and other data sources.

geopy includes geocoder classes for the `OpenStreetMap Nominatim`_,
`ESRI ArcGIS`_, `Google Geocoding API (V3)`_, `Baidu Maps`_,
`Bing Maps API`_, `Yandex`_, `IGN France`_, `GeoNames`_,
`Pelias`_, `geocode.earth`_,
`OpenMapQuest`_, `PickPoint`_, `What3Words`_, `OpenCage`_,
`SmartyStreets`_, `GeocodeFarm`_, `Here`_ and `MapBox`_ geocoder services.
The various geocoder classes are located in `geopy.geocoders`_.

.. _OpenStreetMap Nominatim: https://wiki.openstreetmap.org/wiki/Nominatim
.. _ESRI ArcGIS: http://resources.arcgis.com/en/help/arcgis-rest-api/
.. _Google Geocoding API (V3): https://developers.google.com/maps/documentation/geocoding/
.. _Baidu Maps: http://developer.baidu.com/map/webservice-geocoding.htm
.. _Bing Maps API: http://www.microsoft.com/maps/developers/web.aspx
.. _Yandex: http://api.yandex.com/maps/doc/intro/concepts/intro.xml
.. _IGN France: http://api.ign.fr/tech-docs-js/fr/developpeur/search.html
.. _GeoNames: http://www.geonames.org/
.. _Pelias: https://pelias.io/
.. _geocode.earth: https://geocode.earth/
.. _OpenMapQuest: http://developer.mapquest.com/web/products/open/geocoding-service
.. _PickPoint: https://pickpoint.io
.. _What3Words: http://what3words.com/api/reference
.. _OpenCage: https://geocoder.opencagedata.com/
.. _SmartyStreets: https://smartystreets.com/products/liveaddress-api
.. _GeocodeFarm: https://www.geocodefarm.com/
.. _Here: https://developer.here.com/documentation/geocoder/
.. _MapBox: https://www.mapbox.com/api-documentation/#geocoding
.. _geopy.geocoders: https://github.com/geopy/geopy/tree/master/geopy/geocoders

geopy is tested against CPython (versions 2.7, 3.4, 3.5, 3.6, 3.7), PyPy, and
PyPy3. geopy does not and will not support CPython 2.6.

© geopy contributors 2006-2018 (see AUTHORS) under the `MIT
License <https://github.com/geopy/geopy/blob/master/LICENSE>`__.

Installation
------------

Install using `pip <http://www.pip-installer.org/en/latest/>`__ with:

::

    pip install geopy

Or, `download a wheel or source archive from
PyPI <https://pypi.python.org/pypi/geopy>`__.

Geocoding
---------

To geolocate a query to an address and coordinates:

.. code:: python

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

.. code:: python

    >>> from geopy.geocoders import Nominatim
    >>> geolocator = Nominatim(user_agent="specify_your_app_name_here")
    >>> location = geolocator.reverse("52.509669, 13.376294")
    >>> print(location.address)
    Potsdamer Platz, Mitte, Berlin, 10117, Deutschland, European Union
    >>> print((location.latitude, location.longitude))
    (52.5094982, 13.3765983)
    >>> print(location.raw)
    {'place_id': '654513', 'osm_type': 'node', ...}

Measuring Distance
------------------

Geopy can calculate geodesic distance between two points using the
`geodesic distance
<https://en.wikipedia.org/wiki/Geodesics_on_an_ellipsoid>`_ or the
`great-circle distance
<https://en.wikipedia.org/wiki/Great-circle_distance>`_,
with a default of the geodesic distance available as the function
`geopy.distance.distance`.

Here's an example usage of the geodesic distance:

.. code:: python

    >>> from geopy.distance import geodesic
    >>> newport_ri = (41.49008, -71.312796)
    >>> cleveland_oh = (41.499498, -81.695391)
    >>> print(geodesic(newport_ri, cleveland_oh).miles)
    538.390445368

Using great-circle distance:

.. code:: python

    >>> from geopy.distance import great_circle
    >>> newport_ri = (41.49008, -71.312796)
    >>> cleveland_oh = (41.499498, -81.695391)
    >>> print(great_circle(newport_ri, cleveland_oh).miles)
    536.997990696

Documentation
-------------

More documentation and examples can be found at
`Read the Docs <http://geopy.readthedocs.io/en/latest/>`__.
