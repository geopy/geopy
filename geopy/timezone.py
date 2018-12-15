from geopy.compat import text_type
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
    if not pytz_available:
        raise ImportError(
            'pytz must be installed in order to locate timezones. '
            ' Install with `pip install geopy -e ".[timezone]"`.'
        )


def from_timezone_name(timezone_name, raw=None):
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


def from_fixed_gmt_offset(gmt_offset_hours, raw=None):
    ensure_pytz_is_installed()
    pytz_timezone = pytz.FixedOffset(gmt_offset_hours * 60)
    return Timezone(pytz_timezone, raw)


class Timezone(object):
    """
    Contains a parsed response for a timezone request, which is
    implemented in few geocoders which provide such lookups.

    .. versionadded:: 1.18.0
    """

    __slots__ = ("_pytz_timezone", "_raw")

    def __init__(self, pytz_timezone, raw=None):
        self._pytz_timezone = pytz_timezone
        self._raw = raw

    @property
    def pytz_timezone(self):
        """
        pytz timezone instance.

        :rtype: :class:`pytz.tzinfo.BaseTzInfo`
        """
        return self._pytz_timezone

    @property
    def raw(self):
        """
        Timezone's raw, unparsed geocoder response. For details on this,
        consult the service's documentation.

        :rtype: dict or None
        """
        return self._raw

    def __unicode__(self):
        return text_type(self._pytz_timezone)

    __str__ = __unicode__

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
