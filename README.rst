geopy
=====

.. image:: https://img.shields.io/pypi/v/geopy.svg?style=flat-square
    :target: https://pypi.python.org/pypi/geopy/
    :alt: Latest Version

.. image:: https://img.shields.io/github/actions/workflow/status/geopy/geopy/ci.yml?branch=master&style=flat-square
    :target: https://github.com/geopy/geopy/actions/workflows/ci.yml?query=branch%3Amaster
    :alt: Build Status

.. image:: https://img.shields.io/github/license/geopy/geopy.svg?style=flat-square
    :target: https://pypi.python.org/pypi/geopy/
    :alt: License


geopy is a Python client for several popular geocoding web
services.

geopy makes it easy for Python developers to locate the coordinates of
addresses, cities, countries, and landmarks across the globe using
third-party geocoders and other data sources.

geopy includes geocoder classes for the `OpenStreetMap Nominatim`_,
`Google Geocoding API (V3)`_, and many other geocoding services.
The full list is available on the `Geocoders doc section`_.
Geocoder classes are located in `geopy.geocoders`_.

.. _OpenStreetMap Nominatim: https://nominatim.org
.. _Google Geocoding API (V3): https://developers.google.com/maps/documentation/geocoding/
.. _Geocoders doc section: https://geopy.readthedocs.io/en/latest/#geocoders
.. _geopy.geocoders: https://github.com/geopy/geopy/tree/master/geopy/geocoders

geopy is tested against CPython (versions 3.7, 3.8, 3.9, 3.10, 3.11, 3.12)
and PyPy3. geopy 1.x line also supported CPython 2.7, 3.4 and PyPy2.

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

.. code:: pycon

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

.. code:: pycon

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

Here's an example usage of the geodesic distance, taking pair
of :code:`(lat, lon)` tuples:

.. code:: pycon

    >>> from geopy.distance import geodesic
    >>> newport_ri = (41.49008, -71.312796)
    >>> cleveland_oh = (41.499498, -81.695391)
    >>> print(geodesic(newport_ri, cleveland_oh).miles)
    538.390445368

Using great-circle distance, also taking pair of :code:`(lat, lon)` tuples:

.. code:: pycon

    >>> from geopy.distance import great_circle
    >>> newport_ri = (41.49008, -71.312796)
    >>> cleveland_oh = (41.499498, -81.695391)
    >>> print(great_circle(newport_ri, cleveland_oh).miles)
    536.997990696

Documentation
-------------

More documentation and examples can be found at
`Read the Docs <http://geopy.readthedocs.io/en/latest/>`__.
