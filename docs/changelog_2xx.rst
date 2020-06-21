:orphan:

Changelog
=========

.. _v2-0-0:

2.0.0
-----
2020-XXX

geopy 2.0 is a major release with lots of cleanup and inner refactorings.
The public interface of the library is mostly the same, and the set
of supported geocoders didn't change.

If you have checked your code on the latest 1.x release with enabled
warnings (i.e. with ``-Wd`` key of the ``python`` command) and fixed
all of them, then it should be safe to upgrade.

New features
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

Packaging changes
~~~~~~~~~~~~~~~~~

- Dropped support for Python 2.7 and 3.4.
- New extras:

  + ``geopy[requests]`` for :class:`geopy.adapters.RequestsAdapter`.
  + ``geopy[aiohttp]`` for :class:`geopy.adapters.AioHTTPAdapter`.

Chores
~~~~~~

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
