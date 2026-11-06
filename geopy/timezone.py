from geopy.exc import GeocoderParseError

try:
    import pytz
    pytz_available = True
except ImportError:
    pytz_available = False


__all__ = (
    "Timezone",
)


def ensure_pytz_is_installed():
    """
    Check that :mod:`pytz` is installed.

    Timezone lookups require :mod:`pytz`, which is an optional
    dependency of geopy. Raise ``ImportError`` if it is not
    installed. It can be installed with
    ``pip install "geopy[timezone]"``.
    """
    if not pytz_available:
        raise ImportError(
            'pytz must be installed in order to locate timezones. '
            'If geopy has been installed with `pip`, then pytz can be '
            'installed with `pip install "geopy[timezone]"`.'
        )


def from_timezone_name(timezone_name, raw):
    """
    Create a :class:`Timezone` from a timezone name.

    :param str timezone_name: A timezone identifier, such as an
        IANA/Olson database name (e.g. ``"Europe/Paris"``), as
        returned by a geocoding service.
    :param raw: The raw, unparsed geocoder response the timezone
        was extracted from.
    :return: A timezone for the given name.
    :rtype: :class:`Timezone`

    Raise :class:`~geopy.exc.GeocoderParseError` if ``pytz`` cannot
    parse the timezone name, or if no timezone could be found in
    the response.
    """
    ensure_pytz_is_installed()
    try:
        pytz_timezone = pytz.timezone(timezone_name)
    except pytz.UnknownTimeZoneError:
        raise GeocoderParseError(
            "pytz could not parse the timezone identifier (%s) "
            "returned by the service." % timezone_name
        )
    except KeyError:
        raise GeocoderParseError(
            "geopy could not find a timezone in this response: %s" %
            raw
        )
    return Timezone(pytz_timezone, raw)


def from_fixed_gmt_offset(gmt_offset_hours, raw):
    """
    Create a :class:`Timezone` from a fixed offset from GMT.

    Use this when a geocoding service returns a numeric GMT offset
    instead of a timezone name. The resulting timezone has a fixed
    offset and does not observe daylight saving time.

    :param float gmt_offset_hours: Offset from GMT in hours, e.g.
        ``3.0`` for a timezone three hours ahead of GMT. Fractional
        values are supported, e.g. ``5.5`` for UTC+05:30.
    :param raw: The raw, unparsed geocoder response the offset
        was extracted from.
    :return: A timezone with the given fixed offset from GMT.
    :rtype: :class:`Timezone`
    """
    ensure_pytz_is_installed()
    pytz_timezone = pytz.FixedOffset(gmt_offset_hours * 60)
    return Timezone(pytz_timezone, raw)


class Timezone:
    """
    Contains a parsed response for a timezone request, which is
    implemented in a few geocoders that provide such lookups.
    """

    __slots__ = ("_pytz_timezone", "_raw")

    def __init__(self, pytz_timezone, raw):
        self._pytz_timezone = pytz_timezone
        self._raw = raw

    @property
    def pytz_timezone(self):
        """
        A pytz timezone instance.

        :rtype: :class:`pytz.tzinfo.BaseTzInfo`
        """
        return self._pytz_timezone

    @property
    def raw(self):
        """
        Timezone's raw, unparsed geocoder response. For details on this,
        consult the service's documentation.

        :rtype: dict
        """
        return self._raw

    def __str__(self):
        return str(self._pytz_timezone)

    def __repr__(self):
        return "Timezone(%s)" % repr(self.pytz_timezone)

    def __getstate__(self):
        return self._pytz_timezone, self._raw

    def __setstate__(self, state):
        self._pytz_timezone, self._raw = state

    def __eq__(self, other):
        return (
            isinstance(other, Timezone) and
            self._pytz_timezone == other._pytz_timezone and
            self.raw == other.raw
        )

    def __ne__(self, other):
        return not (self == other)
