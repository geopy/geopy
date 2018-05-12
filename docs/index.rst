Welcome to GeoPy's documentation!
=================================

.. automodule:: geopy
   :members: __doc__

Geocoders
~~~~~~~~~

.. automodule:: geopy.geocoders
   :members: __doc__

.. autoclass:: geopy.geocoders.options
   :members:
   :undoc-members:

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

.. autoclass:: geopy.geocoders.GeoNames
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.GoogleV3
    :members: __init__, geocode, reverse, timezone

.. autoclass:: geopy.geocoders.IGNFrance
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.Mapzen
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.OpenCage
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.OpenMapQuest
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.Nominatim
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.Photon
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.PickPoint
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.LiveAddress
    :members: __init__, geocode

.. autoclass:: geopy.geocoders.What3Words
    :members: __init__, geocode, reverse

.. autoclass:: geopy.geocoders.Yandex
    :members: __init__, geocode, reverse

Calculating Distance
~~~~~~~~~~~~~~~~~~~~

.. automodule:: geopy.distance
    :members: __doc__

.. autofunction:: geopy.distance.lonlat

.. autoclass:: geopy.distance.geodesic
    :members: __init__

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
    :show-inheritance:

.. autoclass:: geopy.exc.ConfigurationError
    :show-inheritance:

.. autoclass:: geopy.exc.GeocoderServiceError
    :show-inheritance:

.. autoclass:: geopy.exc.GeocoderQueryError
    :show-inheritance:

.. autoclass:: geopy.exc.GeocoderQuotaExceeded
    :show-inheritance:

.. autoclass:: geopy.exc.GeocoderAuthenticationFailure
    :show-inheritance:

.. autoclass:: geopy.exc.GeocoderInsufficientPrivileges
    :show-inheritance:

.. autoclass:: geopy.exc.GeocoderTimedOut
    :show-inheritance:

.. autoclass:: geopy.exc.GeocoderUnavailable
    :show-inheritance:

.. autoclass:: geopy.exc.GeocoderParseError
    :show-inheritance:

.. autoclass:: geopy.exc.GeocoderNotFound
    :show-inheritance:


Logging
~~~~~~~

geopy will log geocoding URLs with a logger name ``geopy`` at level `DEBUG`,
and for some geocoders, these URLs will include authentication information.
Default logging level is `NOTSET`, which delegates the messages processing to
the root logger. See docs for :meth:`logging.Logger.setLevel` for more
information.
geopy does no logging above `DEBUG`.


Changelog
~~~~~~~~~

:doc:`Changelog <changelog_1xx>`.

For changes in the 0.9 series, see the
:doc:`0.9x changelog <changelog_09x>`.


Indices and search
==================

* :ref:`genindex`
* :ref:`search`

