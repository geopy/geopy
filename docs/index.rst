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
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.AzureMaps
   :members:
   :inherited-members:
   :show-inheritance:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.Baidu
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.Bing
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.DataBC
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.GeocodeFarm
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.GeoNames
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.GoogleV3
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.IGNFrance
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.Mapzen
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.OpenCage
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.OpenMapQuest
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.Nominatim
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.Photon
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.PickPoint
   :members:
   :inherited-members:
   :show-inheritance:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.LiveAddress
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.TomTom
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.What3Words
   :members:

   .. automethod:: __init__

.. autoclass:: geopy.geocoders.Yandex
   :members:

   .. automethod:: __init__

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


Semver
~~~~~~

geopy attempts to follow semantic versioning, however some breaking changes
are still being made in minor releases, such as:

- Backwards-incompatible changes of the undocumented API. This shouldn't
  affect anyone, unless they extend geocoder classes or use undocumented
  features or monkey-patch anything. If you believe that something is
  missing in geopy, please consider opening an issue or providing a patch
  or a PR instead of hacking around geopy.

- Geocoder classes which simply don't work (usually because their service
  has been discontinued) might get removed. They don't work anyway, so
  that's hardly a breaking change, right? :)

- Geocoding services sometimes introduce new APIs and deprecate the previous
  ones. We try to upgrade without breaking the geocoder's API interface,
  but the :attr:`geopy.location.Location.raw` value might change in a
  backwards-incompatible way.

- Behavior for invalid input and peculiar edge cases might be altered.
  For example, :class:`geopy.point.Point` instances did coordinate values
  normalization, though it's not documented, and it was completely wrong
  for the latitudes outside the `[-90; 90]` range. So instead of using an
  incorrectly normalized value for latitude, an :class:`ValueError`
  exception is now thrown (#294).


To make the upgrade less painful, please read the changelog before upgrading.


Changelog
~~~~~~~~~

:doc:`Changelog for 1.x.x series <changelog_1xx>`.

For changes in the 0.9 series, see the
:doc:`0.9x changelog <changelog_09x>`.


Indices and search
==================

* :ref:`genindex`
* :ref:`search`

