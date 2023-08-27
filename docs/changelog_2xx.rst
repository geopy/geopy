:orphan:

Changelog
=========

.. _v2-4-0:

2.4.0
-----
2023-08-27

New Features
~~~~~~~~~~~~

- New geocoder: :class:`.Woosmap`.
  Contributed by galela. (:issue:`541`)
- New geocoder: :class:`.Geokeo`.
  Contributed by Geokeo. (:issue:`490`)

Breaking Changes
~~~~~~~~~~~~~~~~

- Removed Algolia Places geocoder: the service is shut down.
  Contributed by mtmail. (:issue:`547`)

Packaging Changes
~~~~~~~~~~~~~~~~~

- Add support for Python 3.12. (:issue:`559`)
- Update maintainer email.
- GitHub releases are now signed with GPG. (:issue:`550`)
- tests: switch from httpbin.org to httpbingo.org. (:issue:`551`)
- tests: use tox ``allowlist_externals`` instead of ``whitelist_externals``.
  Contributed by galela. (:issue:`540`)

Bugfixes
~~~~~~~~

- RequestsAdapter: use system CA store by default instead of ``certifi``.
  (:issue:`558`)
- :class:`.DataBC`: update service domain and endpoint.
  Contributed by nickpcrogers. (:issue:`557`)

Code Improvements
~~~~~~~~~~~~~~~~~

- Move hardcoded domains to ``__init__`` args for all geocoders.


.. _v2-3-0:

2.3.0
-----
2022-11-13

New Features
~~~~~~~~~~~~

- :class:`.MapBox`: add ``referer`` param to allow restricted api_keys.
  Contributed by Dennis Stritzke. (:issue:`501`)
- :class:`.MapBox`: add ``language`` param to ``geocode``.
  Contributed by Dennis Stritzke. (:issue:`503`)
- :class:`.Distance`: add floor division + right multiplication
  operators. (:issue:`485`)
- :class:`.Distance`: make hashable. (:issue:`485`)
- :class:`.Nominatim`: add ``namedetails`` param to ``reverse``. (:issue:`525`)
- :class:`.Pelias`: add ``countries`` param to ``geocode``. (:issue:`504`)
- :class:`.GoogleV3`: pass the original ``error_message`` to exceptions.
  (:issue:`398`)

Packaging Changes
~~~~~~~~~~~~~~~~~

- Drop support for Python 3.5 and 3.6.
- Add support for Python 3.10 and 3.11.
- Relax geographiclib upper version constraint to allow 2.x.
  Contributed by David Hotham. (:issue:`520`)
- Raise geographiclib lower version constraint to 1.52 to fix possible
  :class:`ValueError` in :class:`.distance.geodesic` due to
  the floating point inaccuracy. (:issue:`466`)
- Move static metadata from ``setup.py`` to ``setup.cfg``.

Deprecations
~~~~~~~~~~~~

- :class:`.Pelias`: deprecate ``country_bias`` param, use ``countries``
  instead. (:issue:`504`)
- :class:`.IGNFrance`: authentication is no longer accepted by the API,
  so passing any credentials to the geocoder class has been deprecated.
  These arguments should be removed. (:issue:`496`)

Bugfixes
~~~~~~~~

- Fix possible :class:`TypeError` thrown by :class:`.RequestsAdapter`
  on destruction. Contributed by Philip Kahn. (:issue:`488`)
- :class:`.ArcGIS`: get address from LongLabel if Address is empty.
- All geocoders: fix unexpected scientific point format for coordinates
  near zero in reverse geocoding. (:issue:`511`)
- :class:`.BANFrance`: fix broken reverse (it looks like their API has
  changed in a backwards-incompatible way: the ``lng`` query arg has
  been renamed to ``lon``).
- :class:`.IGNFrance`: fix broken geocoder due to removal of
  authentication in their API. (:issue:`496`)

Docs Improvements
~~~~~~~~~~~~~~~~~

- Add url to the GIS Stack Exchange geopy tag.
  Contributed by Taras Dubrava. (:issue:`516`).
- :class:`.GeocodeEarth`: add docs and pricing urls.
  Contributed by Julian Simioni. (:issue:`505`).


.. _v2-2-0:

2.2.0
-----
2021-07-11

New Features
~~~~~~~~~~~~

- :class:`.OpenCage`: added ``annotations`` param.
  Contributed by mtmail. (:issue:`464`)
- :class:`.Photon`: added ``bbox`` param.
  Contributed by Holger Bruch. (:issue:`472`)
- New geocoder: :class:`.Geocodio`.
  Contributed by Jon Duckworth. (:issue:`468`)
- New geocoder: :class:`.HereV7`.
  Contributed by Pratheek Rebala. (:issue:`433`)
- New geocoder: :class:`.What3WordsV3`.
  Contributed by Saïd Tezel. (:issue:`444`)
- New error class: :class:`.exc.GeocoderRateLimited`. This error extends
  :class:`.exc.GeocoderQuotaExceeded` and is now raised instead of it
  for HTTP 422 error code. (:issue:`479`)
- :class:`.AdapterHTTPError`: added ``headers`` attribute. (:issue:`479`)

Breaking Changes
~~~~~~~~~~~~~~~~

- Removed GeocodeFarm class: the service is very unstable. (:issue:`445`)

Deprecations
~~~~~~~~~~~~

- :class:`.GoogleV3` has been moved from ``geopy.geocoders.googlev3`` module
  to ``geopy.geocoders.google``. The old module is still present for
  backwards compatibility, but it will be removed in geopy 3. (:issue:`483`)

Bugfixes
~~~~~~~~

- :class:`.OpenCage`: improved error handling by using the default errors map
  (e.g. to raise :class:`.exc.GeocoderQuotaExceeded` instead of
  :class:`.exc.GeocoderQueryError` for HTTP 402 error). (:issue:`479`)

Code Improvements
~~~~~~~~~~~~~~~~~

- :class:`.Photon`: updated domain. Contributed by yrafalin. (:issue:`481`)
- :class:`.IGNFrance`: removed redundant check. Contributed by Miltos. (:issue:`469`)
- Changed default exception type for HTTP code 408: now it is raised as
  :class:`.exc.GeocoderTimedOut` instead of a more
  generic :class:`.exc.GeocoderServiceError`. (:issue:`479`)
- :mod:`geopy.exc`: extend more specific built-in exceptions where appropriate:
  classes :class:`.ConfigurationError`, :class:`.GeocoderQueryError`,
  :class:`.GeocoderNotFound` now extend :class:`ValueError`;
  :class:`.GeocoderRateLimited` and :class:`.GeocoderUnavailable`
  extend :class:`IOError`;
  :class:`.GeocoderTimedOut` extends :class:`TimeoutError`. (:issue:`484`)

Docs Improvements
~~~~~~~~~~~~~~~~~

- Be more explicit in lat lon ordering.
  Contributed by Mateusz Konieczny. (:issue:`476`)
- Added tests for geocoders' signatures (to ensure that all parameters
  are documented) and fixed docstrings which didn't pass them. (:issue:`480`)
- Added docs for :class:`.Distance` class
  and :meth:`.Distance.destination` method (:issue:`473`)


.. _v2-1-0:

2.1.0
-----
2020-12-27

New Features
~~~~~~~~~~~~

- Add support for leading plus sign in the :class:`.Point` constructor.
  Contributed by Azimjon Pulatov. (:issue:`448`)

Breaking Changes
~~~~~~~~~~~~~~~~

- :class:`.GoogleV3`: change missing ``api_key`` warning to an error. (:issue:`450`)

Bugfixes
~~~~~~~~

- Fixed an undocumented breaking change in geopy 2.0.0, where
  the :class:`.Distance` class has become abstract, thus it could
  no longer be used for unit conversions. (:issue:`435`)
- :class:`.Photon` incorrectly treated 0.0 coordinate as an empty response.
  Contributed by Mateusz Konieczny. (:issue:`439`)
- :class:`.Nominatim`: fix TypeError on empty ``reverse`` result. (:issue:`455`)


Docs Improvements
~~~~~~~~~~~~~~~~~

- Add Python 3.9 to the list of supported versions.
- :class:`.Bing`: change ``postalcode`` to ``postalCode``.
  Contributed by zhongjun-ma. (:issue:`424`)
- :class:`.Nominatim`: better describe what is returned in addressdetails.
  Contributed by Mateusz Konieczny. (:issue:`429`)
- :class:`.Nominatim`: better describe ``viewbox`` param behavior.
  Contributed by Hannes. (:issue:`454`)
- :class:`.Yandex`: remove attention block about requiring an API key.


.. _v2-0-0:

2.0.0
-----
2020-06-27

geopy 2.0 is a major release with lots of cleanup and inner refactorings.
The public interface of the library is mostly the same, and the set
of supported geocoders didn't change.

If you have checked your code on the latest 1.x release with enabled
warnings (i.e. with ``-Wd`` key of the ``python`` command) and fixed
all of them, then it should be safe to upgrade.

New Features
~~~~~~~~~~~~

- :mod:`geopy.adapters` module. Previously all geocoders used :mod:`urllib`
  for HTTP requests, which doesn't support keepalives. Adapters is
  a new mechanism which allows to use other HTTP client implementations.

  There are 3 implementations coming out of the box:

  + :class:`geopy.adapters.RequestsAdapter` -- uses ``requests`` library
    which supports keepalives (thus it is significantly more effective
    than ``urllib``). It is used by default if ``requests`` package
    is installed.
  + :class:`geopy.adapters.URLLibAdapter` -- uses ``urllib``, basically
    it provides the same behavior as in geopy 1.x. It is used by default if
    ``requests`` package is not installed.
  + :class:`geopy.adapters.AioHTTPAdapter` -- uses ``aiohttp`` library.

- Added optional asyncio support in all geocoders via
  :class:`.AioHTTPAdapter`, see the new :ref:`Async Mode <async_mode>`
  doc section.
- :class:`.AsyncRateLimiter` -- an async counterpart of :class:`.RateLimiter`.
- :class:`.RateLimiter` is now thread-safe.

Packaging Changes
~~~~~~~~~~~~~~~~~

- Dropped support for Python 2.7 and 3.4.
- New extras:

  + ``geopy[requests]`` for :class:`geopy.adapters.RequestsAdapter`.
  + ``geopy[aiohttp]`` for :class:`geopy.adapters.AioHTTPAdapter`.

Breaking Changes
~~~~~~~~~~~~~~~~

- ``geopy.distance`` algorithms now raise ``ValueError`` for points with
  different altitudes, because :ref:`altitude is ignored in calculations
  <distance_altitudes>`.
- Removed ``geopy.distance.vincenty``, use :class:`geopy.distance.geodesic` instead.
- ``timeout=None`` now disables request timeout, previously
  a default timeout has been used in this case.
- Removed ``GoogleV3.timezone``, use :meth:`.GoogleV3.reverse_timezone` instead.
- Removed ``format_string`` param from all geocoders.
  See :ref:`Specifying Parameters Once <specifying_parameters_once>`
  doc section for alternatives.
- ``exactly_one``'s default is now ``True`` for all geocoders
  and methods.
- Removed service-specific request params from all ``__init__`` methods
  of geocoders. Pass them to the corresponding ``geocode``/``reverse``
  methods instead.
- All bounding box arguments now must be passed as a list of two Points.
  Previously some geocoders accepted unique formats like plain strings
  and lists of 4 coordinates -- these values are not valid anymore.
- :meth:`.GoogleV3.reverse_timezone` used to allow numeric ``at_time`` value.
  Pass ``datetime`` instances instead.
- ``reverse`` methods used to bypass the query if it couldn't be parsed
  as a :class:`.Point`. Now a ``ValueError`` is raised in this case.
- :class:`.Location` and :class:`.Timezone` classes no longer accept None
  for ``point`` and ``raw`` args.
- :class:`.Nominatim` now raises :class:`geopy.exc.ConfigurationError` when
  used with a default or sample user-agent.
- :class:`.Point` now raises a ``ValueError`` if constructed from a single number.
  A zero longitude must be explicitly passed to avoid the error.
- Most of the service-specific arguments of geocoders now must be passed
  as kwargs, positional arguments are not accepted.
- Removed default value ``None`` for authentication key arguments of
  :class:`.GeoNames`, :class:`.OpenMapQuest` and :class:`.Yandex`.
- ``parse_*`` methods in geocoders have been prefixed with ``_``
  to explicitly mark that they are private.

Deprecations
~~~~~~~~~~~~

- :class:`.Nominatim` has been moved from ``geopy.geocoders.osm`` module
  to ``geopy.geocoders.nominatim``. The old module is still present for
  backwards compatibility, but it will be removed in geopy 3.
