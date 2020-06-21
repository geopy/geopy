:orphan:

Changelog
=========

.. _v2-0-0:

2.0.0
-----
2020-XXX

Packaging changes
~~~~~~~~~~~~~~~~~

- Dropped support for Python 2.7 and 3.4.

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
