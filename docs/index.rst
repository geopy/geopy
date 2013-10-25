.. GeoPy documentation master file, created by
   sphinx-quickstart on Thu Oct 24 19:28:11 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to GeoPy's documentation!
=================================

.. automodule:: geopy
   :members: __doc__

Geocoders
~~~~~~~~~
Geocoders each define at least a ``geocode`` method, for resolving a location
from a string, and may define a ``reverse`` method, which resolves a pair of
coordinates to an address. Each Geocoder accepts any credentials
or settings needed to interact with its service, e.g., an API key or
locale, during its initialization.

.. autoclass:: geopy.geocoders.Bing
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.GoogleV3
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.GeocoderDotUS
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.GeoNames
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.MapQuest
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.OpenMapQuest
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.MediaWiki
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.YahooPlaceFinder
    :members: __init__, geocode

Data
~~~~

.. autoclass:: geopy.point.Point
    :members: __new__, from_string, from_sequence, from_point

Indices and search
==================

* :ref:`genindex`
* :ref:`search`

