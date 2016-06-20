Welcome to GeoPy's documentation!
=================================

.. automodule:: geopy
   :members: __doc__

Geocoders
~~~~~~~~~

.. automodule:: geopy.geocoders
   :members: __doc__

.. autofunction:: geopy.geocoders.get_geocoder_for_service

.. autoclass:: geopy.geocoders.ArcGIS
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.Baidu
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.Bing
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.DataBC
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.GeocodeFarm
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.GeocoderDotUS
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.GeoNames
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.GoogleV3
    :members: __init__, geocode, reverse, timezone

.. autoclass:: geopy.geocoders.IGNFrance
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.LiveAddress
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.MapQuest
    :members: __init__, geocode, reverse
    
.. autoclass:: geopy.geocoders.Mapzen
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.NaviData
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.Nominatim
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.OpenCage
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.OpenMapQuest
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.Photon
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.What3Words
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.Yandex
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

.. autoclass:: geopy.exc.GeocoderUnavailable

.. autoclass:: geopy.exc.GeocoderParseError

.. autoclass:: geopy.exc.GeocoderNotFound


Logging
~~~~~~~

geopy will log geocoding URLs with a logger name `geopy` at level `DEBUG`,
and for some geocoders, these URLs will include authentication information.
If this is a concern, one can disable this logging by specifying a logging
level of `NOTSET` or a level greater than `DEBUG` for logger name `geopy`.
geopy does no logging above DEBUG.


Changelog
~~~~~~~~~

.. include:: changelog_1xx.rst

For changes in the 0.9 series, see the
:doc:`0.9x changelog <changelog_09x>`.


Indices and search
==================

* :ref:`genindex`
* :ref:`search`

