import collections.abc

from geopy.point import Point


def _location_tuple(location):
    return location._address, (location._point[0], location._point[1])


class Location:
    """
    Contains a parsed geocoder response. Can be iterated over as
    ``(location<String>, (latitude<float>, longitude<Float))``.
    Or one can access the properties ``address``, ``latitude``,
    ``longitude``, or ``raw``. The last
    is a dictionary of the geocoder's response for this item.
    """

    __slots__ = ("_address", "_point", "_tuple", "_raw")

    def __init__(self, address, point, raw):
        if address is None:
            raise TypeError("`address` must not be None")
        self._address = address

        if isinstance(point, Point):
            self._point = point
        elif isinstance(point, str):
            self._point = Point(point)
        elif isinstance(point, collections.abc.Sequence):
            self._point = Point(point)
        else:
            raise TypeError(
                "`point` is of unsupported type: %r" % type(point)
            )
        self._tuple = _location_tuple(self)

        if raw is None:
            raise TypeError("`raw` must not be None")
        self._raw = raw

    @property
    def address(self):
        """
        Location as a formatted string returned by the geocoder or constructed
        by geopy, depending on the service.

        :rtype: str
        """
        return self._address

    @property
    def latitude(self):
        """
        Location's latitude.

        :rtype: float
        """
        return self._point[0]

    @property
    def longitude(self):
        """
        Location's longitude.

        :rtype: float
        """
        return self._point[1]

    @property
    def altitude(self):
        """
        Location's altitude.

        .. note::
            Geocoding services usually don't consider altitude neither in
            requests nor in responses, so almost always the value of this
            property would be zero.

        :rtype: float
        """
        return self._point[2]

    @property
    def point(self):
        """
        :class:`geopy.point.Point` instance representing the location's
        latitude, longitude, and altitude.

        :rtype: :class:`geopy.point.Point`
        """
        return self._point

    @property
    def raw(self):
        """
        Location's raw, unparsed geocoder response. For details on this,
        consult the service's documentation.

        :rtype: dict
        """
        return self._raw

    def __getitem__(self, index):
        """
        Backwards compatibility with geopy<0.98 tuples.
        """
        return self._tuple[index]

    def __str__(self):
        return self._address

    def __repr__(self):
        return "Location(%s, (%s, %s, %s))" % (
            self._address, self.latitude, self.longitude, self.altitude
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
            self._address == other._address and
            self._point == other._point and
            self.raw == other.raw
        )

    def __ne__(self, other):
        return not (self == other)

    def __len__(self):
        return len(self._tuple)
