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

.. automodule:: geopy.geocoders
   :members: __doc__

.. autoclass:: geopy.geocoders.ArcGIS
    :members: __init__, geocode, reverse

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

.. autoclass:: geopy.geocoders.Nominatim
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.OpenMapQuest
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.YahooPlaceFinder
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.GeocodeFarm
    :members: __init__, geocode, reverse

Calculating Distance
~~~~~~~~~~~~~~~~~~~~

.. automodule:: geopy.distance
    :members: __doc__

.. autoclass:: geopy.distance.vincenty
    :members: __init__

.. autoclass:: geopy.distance.great_circle
    :members: __init__

Data
~~~~

.. autoclass:: geopy.location.Location
    :members: __init__, address, latitude, longitude, altitude, raw

.. autoclass:: geopy.point.Point
    :members: __new__, from_string, from_sequence, from_point

Exceptions
~~~~~~~~~~

.. autoclass:: geopy.exc.GeopyError

.. autoclass:: geopy.exc.ConfigurationError

.. autoclass:: geopy.exc.GeocoderServiceError

.. autoclass:: geopy.exc.GeocoderQueryError

.. autoclass:: geopy.exc.GeocoderQuotaExceeded

.. autoclass:: geopy.exc.GeocoderAuthenticationFailure

.. autoclass:: geopy.exc.GeocoderInsufficientPrivileges

.. autoclass:: geopy.exc.GeocoderTimedOut

.. autoclass:: geopy.exc.GeocoderParseError

Logging
~~~~~~~

geopy will log geocoding URLs with a logger name `geopy` at level `DEBUG`,
and for some geocoders, these URLs will include authentication information.
If this is a concern, one can disable this logging by specifying a logging
level of `NOTSET` or a level greater than `DEBUG` for logger name `geopy`.
geopy does no logging above DEBUG.


Indices and search
==================

* :ref:`genindex`
* :ref:`search`

