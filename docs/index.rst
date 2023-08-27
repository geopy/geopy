Welcome to GeoPy's documentation!
=================================

.. image:: _static/logo-wide.png
   :width: 80%
   :align: center
   :alt: GeoPy logo

:Documentation: https://geopy.readthedocs.io/
:Source Code: https://github.com/geopy/geopy
:Stack Overflow: https://stackoverflow.com/questions/tagged/geopy
:GIS Stack Exchange: https://gis.stackexchange.com/questions/tagged/geopy
:Discussions: https://github.com/geopy/geopy/discussions
:Issue Tracker: https://github.com/geopy/geopy/issues
:PyPI: https://pypi.org/project/geopy/

.. automodule:: geopy
   :members: __doc__

.. toctree::
    :maxdepth: 3
    :caption: Contents

    index


Installation
~~~~~~~~~~~~

::

    pip install geopy

Geocoders
~~~~~~~~~

.. automodule:: geopy.geocoders
   :members: __doc__

Accessing Geocoders
-------------------

The typical way of retrieving a geocoder class is to make an import
from ``geopy.geocoders`` package::

    from geopy.geocoders import Nominatim

.. autofunction:: geopy.geocoders.get_geocoder_for_service

Default Options Object
----------------------

.. autoclass:: geopy.geocoders.options
   :members:
   :undoc-members:

Usage with Pandas
-----------------

It is possible to geocode a pandas DataFrame with geopy, however,
rate-limiting must be taken into account.

A large number of DataFrame rows might produce a significant amount of
geocoding requests to a Geocoding service, which might be throttled
by the service (e.g. by returning `Too Many Requests` 429 HTTP error
or timing out).

:mod:`geopy.extra.rate_limiter` classes provide a convenient
wrapper, which can be used to automatically add delays between geocoding
calls to reduce the load on the Geocoding service. Also it can retry
failed requests and swallow errors for individual rows.

If you're having the `Too Many Requests` error, you may try the following:

- Use :mod:`geopy.extra.rate_limiter` with non-zero
  ``min_delay_seconds``.
- Try a different Geocoding service (please consult with their ToS first,
  as some services prohibit bulk geocoding).
- Take a paid plan on the chosen Geocoding service, which provides
  higher quota.
- Provision your own local copy of the Geocoding service (such as Nominatim).

Rate Limiter
++++++++++++

.. automodule:: geopy.extra.rate_limiter
   :members: __doc__

.. autoclass:: geopy.extra.rate_limiter.RateLimiter

   .. automethod:: __init__

.. autoclass:: geopy.extra.rate_limiter.AsyncRateLimiter

   .. automethod:: __init__

ArcGIS
------

.. autoclass:: geopy.geocoders.ArcGIS
   :members:

   .. automethod:: __init__

AzureMaps
---------

.. autoclass:: geopy.geocoders.AzureMaps
   :members:
   :inherited-members:
   :show-inheritance:

   .. automethod:: __init__

Baidu
-----

.. autoclass:: geopy.geocoders.Baidu
   :members:

   .. automethod:: __init__

BaiduV3
-------

.. autoclass:: geopy.geocoders.BaiduV3
   :members:
   :inherited-members:
   :show-inheritance:

   .. automethod:: __init__

BANFrance
---------

.. autoclass:: geopy.geocoders.BANFrance
   :members:

   .. automethod:: __init__

Bing
----

.. autoclass:: geopy.geocoders.Bing
   :members:

   .. automethod:: __init__

DataBC
------

.. autoclass:: geopy.geocoders.DataBC
   :members:

   .. automethod:: __init__

GeocodeEarth
------------

.. autoclass:: geopy.geocoders.GeocodeEarth
   :members:
   :inherited-members:
   :show-inheritance:

   .. automethod:: __init__

GeocodeFarm
-----------

.. versionchanged:: 2.2
   This class has been removed, because the service is too unreliable.
   See :issue:`445`.

Geocodio
--------

.. autoclass:: geopy.geocoders.Geocodio
   :members:

   .. automethod:: __init__

Geokeo
------------

.. autoclass:: geopy.geocoders.Geokeo
   :members:

   .. automethod:: __init__

Geolake
--------

.. autoclass:: geopy.geocoders.Geolake
   :members:

   .. automethod:: __init__

GeoNames
--------

.. autoclass:: geopy.geocoders.GeoNames
   :members:

   .. automethod:: __init__

GoogleV3
--------

.. autoclass:: geopy.geocoders.GoogleV3
   :members:

   .. automethod:: __init__

HERE
----

.. autoclass:: geopy.geocoders.Here
   :members:

   .. automethod:: __init__

HEREv7
------

.. autoclass:: geopy.geocoders.HereV7
   :members:

   .. automethod:: __init__

IGNFrance
---------

.. autoclass:: geopy.geocoders.IGNFrance
   :members:

   .. automethod:: __init__

MapBox
--------

.. autoclass:: geopy.geocoders.MapBox
   :members:

   .. automethod:: __init__

MapQuest
--------

.. autoclass:: geopy.geocoders.MapQuest
   :members:

   .. automethod:: __init__

MapTiler
--------

.. autoclass:: geopy.geocoders.MapTiler
   :members:

   .. automethod:: __init__

OpenCage
--------

.. autoclass:: geopy.geocoders.OpenCage
   :members:

   .. automethod:: __init__

OpenMapQuest
------------

.. autoclass:: geopy.geocoders.OpenMapQuest
   :members:
   :inherited-members:
   :show-inheritance:

   .. automethod:: __init__

Nominatim
---------

.. autoclass:: geopy.geocoders.Nominatim
   :members:

   .. automethod:: __init__

Pelias
------

.. autoclass:: geopy.geocoders.Pelias
   :members:

   .. automethod:: __init__

Photon
------

.. autoclass:: geopy.geocoders.Photon
   :members:

   .. automethod:: __init__

PickPoint
---------

.. autoclass:: geopy.geocoders.PickPoint
   :members:
   :inherited-members:
   :show-inheritance:

   .. automethod:: __init__

LiveAddress
-----------

.. autoclass:: geopy.geocoders.LiveAddress
   :members:

   .. automethod:: __init__

TomTom
------

.. autoclass:: geopy.geocoders.TomTom
   :members:

   .. automethod:: __init__

What3Words
----------

.. autoclass:: geopy.geocoders.What3Words
   :members:

   .. automethod:: __init__

What3WordsV3
------------

.. autoclass:: geopy.geocoders.What3WordsV3
   :members:

   .. automethod:: __init__

Woosmap
------------

.. autoclass:: geopy.geocoders.Woosmap
   :members:

   .. automethod:: __init__

Yandex
------

.. autoclass:: geopy.geocoders.Yandex
   :members:

   .. automethod:: __init__

Calculating Distance
~~~~~~~~~~~~~~~~~~~~

.. automodule:: geopy.distance
   :members: __doc__

.. autofunction:: geopy.distance.lonlat

.. autoclass:: geopy.distance.Distance
   :members: __init__, destination

.. autoclass:: geopy.distance.geodesic
   :show-inheritance:

.. autoclass:: geopy.distance.great_circle
   :show-inheritance:

Data
~~~~

.. autoclass:: geopy.location.Location
    :members: address, latitude, longitude, altitude, point, raw

.. autoclass:: geopy.point.Point
    :members:

    .. automethod:: __new__

.. autoclass:: geopy.timezone.Timezone
    :members: pytz_timezone, raw

Units Conversion
~~~~~~~~~~~~~~~~

.. automodule:: geopy.units
    :members:

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

.. autoclass:: geopy.exc.GeocoderRateLimited
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

Adapters
~~~~~~~~

.. automodule:: geopy.adapters
    :members: __doc__

Supported Adapters
------------------

.. autoclass:: geopy.adapters.RequestsAdapter
    :show-inheritance:

.. autoclass:: geopy.adapters.URLLibAdapter
    :show-inheritance:

.. autoclass:: geopy.adapters.AioHTTPAdapter
    :show-inheritance:


Base Classes
------------

.. autoclass:: geopy.adapters.AdapterHTTPError
    :show-inheritance:

    .. automethod:: __init__

.. autoclass:: geopy.adapters.BaseAdapter
    :members:

    .. automethod:: __init__

.. autoclass:: geopy.adapters.BaseSyncAdapter
    :show-inheritance:
    :members:

.. autoclass:: geopy.adapters.BaseAsyncAdapter
    :show-inheritance:
    :members:

Logging
~~~~~~~

geopy will log geocoding URLs with a logger name ``geopy`` at level `DEBUG`,
and for some geocoders, these URLs will include authentication information.

HTTP bodies of responses with unsuccessful status codes are logged
with `INFO` level.

Default logging level is `NOTSET`, which delegates the messages processing to
the root logger. See docs for :meth:`logging.Logger.setLevel` for more
information.


Semver
~~~~~~

geopy attempts to follow semantic versioning, however some breaking changes
are still being made in minor releases, such as:

- Backwards-incompatible changes of the undocumented API. This shouldn't
  affect anyone, unless they extend geocoder classes or use undocumented
  features or monkey-patch anything. If you believe that something is
  missing in geopy, please consider opening an issue or providing
  a patch/PR instead of hacking around geopy.

- Geocoding services sometimes introduce new APIs and deprecate the previous
  ones. We try to upgrade without breaking the geocoder's API interface,
  but the :attr:`geopy.location.Location.raw` value might change in a
  backwards-incompatible way.

- Behavior for invalid input and peculiar edge cases might be altered.
  For example, :class:`geopy.point.Point` instances previously did
  coordinate values normalization, though it's not documented, and it was
  completely wrong for the latitudes outside the `[-90; 90]` range.
  So instead of using an incorrectly normalized value for latitude,
  a :class:`ValueError` exception is now thrown (:issue:`294`).

Features and usages being phased out are covered with deprecation :mod:`warnings`
when possible. Make sure to run your python with the ``-Wd`` switch to see
if your code emits the warnings.

To make the upgrade less painful, please read the changelog before upgrading.


Changelog
~~~~~~~~~

:doc:`Changelog for 2.x.x series <changelog_2xx>`.

:doc:`Changelog for 1.x.x series <changelog_1xx>`.

:doc:`Changelog for 0.9x series <changelog_09x>`.


Indices and search
==================

* :ref:`genindex`
* :ref:`search`

