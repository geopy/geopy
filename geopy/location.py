"""
:class:`.Location` returns geocoder results.
"""

from geopy.point import Point
from geopy.compat import string_compare, py3k


def _location_tuple(location):
    return location._address, (location._point[0], location._point[1])


class Location(object): # pylint: disable=R0903,R0921
    """
    Contains a parsed geocoder response. Can be iterated over as
    (location<String>, (latitude<float>, longitude<Float)). Or one can access
    the properties `address`, `latitude`, `longitude`, or `raw`. The last
    is a dictionary of the geocoder's response for this item.

    .. versionadded:: 0.98
    """

    __slots__ = ("_address", "_point", "_tuple", "_raw")

    def __init__(self, address="", point=None, raw=None):
        self._address = address
        if point is None:
            self._point = (None, None, None)
        elif isinstance(point, Point):
            self._point = point
        elif isinstance(point, string_compare):
            self._point = Point(point)
        elif isinstance(point, (tuple, list)):
            self._point = Point(point)
        else:
            raise TypeError(
                "point an unsupported type: %r; use %r or Point",
                type(point), type(string_compare)
            )
        self._tuple = _location_tuple(self)
        self._raw = raw

    @property
    def address(self):
        """
        Location as a formatted string returned by the geocoder or constructed
        by geopy, depending on the service.

        :rtype: unicode
        """
        return self._address

    @property
    def latitude(self):
        """
        Location's latitude.

        :rtype: float or None
        """
        return self._point[0]

    @property
    def longitude(self):
        """
        Location's longitude.

        :rtype: float or None
        """
        return self._point[1]

    @property
    def altitude(self):
        """
        Location's altitude.

        :rtype: float or None
        """
        return self._point[2]

    @property
    def point(self):
        """
        :class:`geopy.point.Point` instance representing the location's
        latitude, longitude, and altitude.

        :rtype: :class:`geopy.point.Point` or None
        """
        return self._point if self._point != (None, None, None) else None

    @property
    def raw(self):
        """
        Location's raw, unparsed geocoder response. For details on this,
        consult the service's documentation.

        :rtype: dict or None
        """
        return self._raw

    def __getitem__(self, index):
        """
        Backwards compatibility with geopy<0.98 tuples.
        """
        return self._tuple[index]

    def __unicode__(self):
        return self._address

    __str__ = __unicode__

    def __repr__(self):
        if py3k:
            return "Location(%s, (%s, %s, %s))" % (
                self._address, self.latitude, self.longitude, self.altitude
            )
        else:
            # Python 2 should not return unicode in __repr__:
            # http://bugs.python.org/issue5876
            return "Location((%s, %s, %s))" % (
                self.latitude, self.longitude, self.altitude
            )

    def __iter__(self):
        return iter(self._tuple)

    def __getstate__(self):
        return self._address, self._point, self._raw

    def __setstate__(self, state):
        self._address, self._point, self._raw = state
        self._tuple = _location_tuple(self)

    def __eq__(self, other):
        return (
            isinstance(other, Location) and
            self._address == other._address and  # pylint: disable=W0212
            self._point == other._point and  # pylint: disable=W0212
            self.raw == other.raw
        )

    def __ne__(self, other):
        return not (self == other)

    def __len__(self):  # pragma: no cover
        return len(self._tuple)

