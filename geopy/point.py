"""
:class:`.Point` data structure.
"""

import collections.abc
import re
import warnings
from itertools import islice
from math import fmod, isfinite

from geopy import units, util
from geopy.format import DEGREE, DOUBLE_PRIME, PRIME, format_degrees, format_distance

POINT_PATTERN = re.compile(r"""
    .*?
    (?P<latitude>
      (?P<latitude_direction_front>[NS])?[ ]*
        (?P<latitude_degrees>-?%(FLOAT)s)(?:[%(DEGREE)sD\*\u00B0\s][ ]*
        (?:(?P<latitude_arcminutes>%(FLOAT)s)[%(PRIME)s'm][ ]*)?
        (?:(?P<latitude_arcseconds>%(FLOAT)s)[%(DOUBLE_PRIME)s"s][ ]*)?
        )?(?P<latitude_direction_back>[NS])?)
    %(SEP)s
    (?P<longitude>
      (?P<longitude_direction_front>[EW])?[ ]*
      (?P<longitude_degrees>-?%(FLOAT)s)(?:[%(DEGREE)sD\*\u00B0\s][ ]*
      (?:(?P<longitude_arcminutes>%(FLOAT)s)[%(PRIME)s'm][ ]*)?
      (?:(?P<longitude_arcseconds>%(FLOAT)s)[%(DOUBLE_PRIME)s"s][ ]*)?
      )?(?P<longitude_direction_back>[EW])?)(?:
    %(SEP)s
      (?P<altitude>
        (?P<altitude_distance>-?%(FLOAT)s)[ ]*
        (?P<altitude_units>km|m|mi|ft|nm|nmi)))?
    \s*$
""" % {
    "FLOAT": r'\d+(?:\.\d+)?',
    "DEGREE": DEGREE,
    "PRIME": PRIME,
    "DOUBLE_PRIME": DOUBLE_PRIME,
    "SEP": r'\s*[,;/\s]\s*',
}, re.VERBOSE | re.UNICODE)


def _normalize_angle(x, limit):
    """
    Normalize angle `x` to be within `[-limit; limit)` range.
    """
    double_limit = limit * 2.0
    modulo = fmod(x, double_limit) or 0.0  # `or 0` is to turn -0 to +0.
    if modulo < -limit:
        return modulo + double_limit
    if modulo >= limit:
        return modulo - double_limit
    return modulo


def _normalize_coordinates(latitude, longitude, altitude):
    latitude = float(latitude or 0.0)
    longitude = float(longitude or 0.0)
    altitude = float(altitude or 0.0)

    is_all_finite = all(isfinite(x) for x in (latitude, longitude, altitude))
    if not is_all_finite:
        raise ValueError('Point coordinates must be finite. %r has been passed '
                         'as coordinates.' % ((latitude, longitude, altitude),))

    if abs(latitude) > 90:
        warnings.warn('Latitude normalization has been prohibited in the newer '
                      'versions of geopy, because the normalized value happened '
                      'to be on a different pole, which is probably not what was '
                      'meant. If you pass coordinates as positional args, '
                      'please make sure that the order is '
                      '(latitude, longitude) or (y, x) in Cartesian terms.',
                      UserWarning, stacklevel=3)
        raise ValueError('Latitude must be in the [-90; 90] range.')

    if abs(longitude) > 180:
        # Longitude normalization is pretty straightforward and doesn't seem
        # to be error-prone, so there's nothing to complain about.
        longitude = _normalize_angle(longitude, 180.0)

    return latitude, longitude, altitude


class Point:
    """
    A geodetic point with latitude, longitude, and altitude.

    Latitude and longitude are floating point values in degrees.
    Altitude is a floating point value in kilometers. The reference level
    is never considered and is thus application dependent, so be consistent!
    The default for all values is 0.

    Points can be created in a number of ways...

    With latitude, longitude, and altitude::

        >>> p1 = Point(41.5, -81, 0)
        >>> p2 = Point(latitude=41.5, longitude=-81)

    With a sequence of 2 to 3 values (latitude, longitude, altitude)::

        >>> p1 = Point([41.5, -81, 0])
        >>> p2 = Point((41.5, -81))

    Copy another `Point` instance::

        >>> p2 = Point(p1)
        >>> p2 == p1
        True
        >>> p2 is p1
        False

    Give a string containing at least latitude and longitude::

        >>> p1 = Point('41.5,-81.0')
        >>> p2 = Point('41.5 N -81.0 W')
        >>> p3 = Point('-41.5 S, 81.0 E, 2.5km')
        >>> p4 = Point('23 26m 22s N 23 27m 30s E 21.0mi')
        >>> p5 = Point('''3 26' 22" N 23 27' 30" E''')

    Point values can be accessed by name or by index::

        >>> p = Point(41.5, -81.0, 0)
        >>> p.latitude == p[0]
        True
        >>> p.longitude == p[1]
        True
        >>> p.altitude == p[2]
        True

    When unpacking (or iterating), a ``(latitude, longitude, altitude)`` tuple is
    returned::

        >>> latitude, longitude, altitude = p

    Textual representations::

        >>> p = Point(41.5, -81.0, 12.3)
        >>> str(p)  # same as `p.format()`
        '41 30m 0s N, 81 0m 0s W, 12.3km'
        >>> p.format_unicode()
        '41° 30′ 0″ N, 81° 0′ 0″ W, 12.3km'
        >>> repr(p)
        'Point(41.5, -81.0, 12.3)'
        >>> repr(tuple(p))
        '(41.5, -81.0, 12.3)'
    """

    __slots__ = ("latitude", "longitude", "altitude")

    POINT_PATTERN = POINT_PATTERN

    def __new__(cls, latitude=None, longitude=None, altitude=None):
        """
        :param float latitude: Latitude of point.
        :param float longitude: Longitude of point.
        :param float altitude: Altitude of point.
        """
        single_arg = latitude is not None and longitude is None and altitude is None
        if single_arg and not isinstance(latitude, util.NUMBER_TYPES):
            arg = latitude
            if isinstance(arg, Point):
                return cls.from_point(arg)
            elif isinstance(arg, str):
                return cls.from_string(arg)
            else:
                try:
                    seq = iter(arg)
                except TypeError:
                    raise TypeError(
                        "Failed to create Point instance from %r." % (arg,)
                    )
                else:
                    return cls.from_sequence(seq)

        if single_arg:
            raise ValueError(
                'A single number has been passed to the Point '
                'constructor. This is probably a mistake, because '
                'constructing a Point with just a latitude '
                'seems senseless. If this is exactly what was '
                'meant, then pass the zero longitude explicitly '
                'to get rid of this error.'
            )

        latitude, longitude, altitude = \
            _normalize_coordinates(latitude, longitude, altitude)

        self = super().__new__(cls)
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        return self

    def __getitem__(self, index):
        return tuple(self)[index]  # tuple handles slices

    def __setitem__(self, index, value):
        point = list(self)
        point[index] = value  # list handles slices
        self.latitude, self.longitude, self.altitude = \
            _normalize_coordinates(*point)

    def __iter__(self):
        return iter((self.latitude, self.longitude, self.altitude))

    def __getstate__(self):
        return tuple(self)

    def __setstate__(self, state):
        self.latitude, self.longitude, self.altitude = state

    def __repr__(self):
        return "Point(%r, %r, %r)" % tuple(self)

    def format(self, altitude=None, deg_char='', min_char='m', sec_char='s'):
        """
        Format decimal degrees (DD) to degrees minutes seconds (DMS)::

            >>> p = Point(41.5, -81.0, 12.3)
            >>> p.format()
            '41 30m 0s N, 81 0m 0s W, 12.3km'
            >>> p = Point(41.5, 0, 0)
            >>> p.format()
            '41 30m 0s N, 0 0m 0s E'

        See also :meth:`.format_unicode`.

        :param bool altitude: Whether to include ``altitude`` value.
            By default it is automatically included if it is non-zero.
        """
        latitude = "%s %s" % (
            format_degrees(abs(self.latitude), symbols={
                'deg': deg_char, 'arcmin': min_char, 'arcsec': sec_char
            }),
            self.latitude >= 0 and 'N' or 'S'
        )
        longitude = "%s %s" % (
            format_degrees(abs(self.longitude), symbols={
                'deg': deg_char, 'arcmin': min_char, 'arcsec': sec_char
            }),
            self.longitude >= 0 and 'E' or 'W'
        )
        coordinates = [latitude, longitude]

        if altitude is None:
            altitude = bool(self.altitude)
        if altitude:
            if not isinstance(altitude, str):
                altitude = 'km'
            coordinates.append(self.format_altitude(altitude))

        return ", ".join(coordinates)

    def format_unicode(self, altitude=None):
        """
        :meth:`.format` with pretty unicode chars for degrees,
        minutes and seconds::

            >>> p = Point(41.5, -81.0, 12.3)
            >>> p.format_unicode()
            '41° 30′ 0″ N, 81° 0′ 0″ W, 12.3km'

        :param bool altitude: Whether to include ``altitude`` value.
            By default it is automatically included if it is non-zero.
        """
        return self.format(
            altitude, DEGREE, PRIME, DOUBLE_PRIME
        )

    def format_decimal(self, altitude=None):
        """
        Format decimal degrees with altitude::

            >>> p = Point(41.5, -81.0, 12.3)
            >>> p.format_decimal()
            '41.5, -81.0, 12.3km'
            >>> p = Point(41.5, 0, 0)
            >>> p.format_decimal()
            '41.5, 0.0'

        :param bool altitude: Whether to include ``altitude`` value.
            By default it is automatically included if it is non-zero.
        """
        coordinates = [str(self.latitude), str(self.longitude)]

        if altitude is None:
            altitude = bool(self.altitude)
        if altitude:
            if not isinstance(altitude, str):
                altitude = 'km'
            coordinates.append(self.format_altitude(altitude))

        return ", ".join(coordinates)

    def format_altitude(self, unit='km'):
        """
        Format altitude with unit::

            >>> p = Point(41.5, -81.0, 12.3)
            >>> p.format_altitude()
            '12.3km'
            >>> p = Point(41.5, -81.0, 0)
            >>> p.format_altitude()
            '0.0km'

        :param str unit: Resulting altitude unit. Supported units
            are listed in :meth:`.from_string` doc.
        """
        return format_distance(self.altitude, unit=unit)

    def __str__(self):
        return self.format()

    def __eq__(self, other):
        if not isinstance(other, collections.abc.Iterable):
            return NotImplemented
        return tuple(self) == tuple(other)

    def __ne__(self, other):
        return not (self == other)

    @classmethod
    def parse_degrees(cls, degrees, arcminutes, arcseconds, direction=None):
        """
        Convert degrees, minutes, seconds and direction (N, S, E, W)
        to a single degrees number.

        :rtype: float
        """
        degrees = float(degrees)
        negative = degrees < 0
        arcminutes = float(arcminutes)
        arcseconds = float(arcseconds)

        if arcminutes or arcseconds:
            more = units.degrees(arcminutes=arcminutes, arcseconds=arcseconds)
            if negative:
                degrees -= more
            else:
                degrees += more

        if direction in [None, 'N', 'E']:
            return degrees
        elif direction in ['S', 'W']:
            return -degrees
        else:
            raise ValueError("Invalid direction! Should be one of [NSEW].")

    @classmethod
    def parse_altitude(cls, distance, unit):
        """
        Parse altitude managing units conversion::

            >>> Point.parse_altitude(712, 'm')
            0.712
            >>> Point.parse_altitude(712, 'km')
            712.0
            >>> Point.parse_altitude(712, 'mi')
            1145.852928

        :param float distance: Numeric value of altitude.
        :param str unit: ``distance`` unit. Supported units
            are listed in :meth:`.from_string` doc.
        """
        if distance is not None:
            distance = float(distance)
            CONVERTERS = {
                'km': lambda d: d,
                'm': lambda d: units.kilometers(meters=d),
                'mi': lambda d: units.kilometers(miles=d),
                'ft': lambda d: units.kilometers(feet=d),
                'nm': lambda d: units.kilometers(nautical=d),
                'nmi': lambda d: units.kilometers(nautical=d)
            }
            try:
                return CONVERTERS[unit](distance)
            except KeyError:
                raise NotImplementedError(
                    'Bad distance unit specified, valid are: %r' %
                    CONVERTERS.keys()
                )
        else:
            return distance

    @classmethod
    def from_string(cls, string):
        """
        Create and return a ``Point`` instance from a string containing
        latitude and longitude, and optionally, altitude.

        Latitude and longitude must be in degrees and may be in decimal form
        or indicate arcminutes and arcseconds (labeled with Unicode prime and
        double prime, ASCII quote and double quote or 'm' and 's'). The degree
        symbol is optional and may be included after the decimal places (in
        decimal form) and before the arcminutes and arcseconds otherwise.
        Coordinates given from south and west (indicated by S and W suffixes)
        will be converted to north and east by switching their signs. If no
        (or partial) cardinal directions are given, north and east are the
        assumed directions. Latitude and longitude must be separated by at
        least whitespace, a comma, or a semicolon (each with optional
        surrounding whitespace).

        Altitude, if supplied, must be a decimal number with given units.
        The following unit abbrevations (case-insensitive) are supported:

            - ``km`` (kilometers)
            - ``m`` (meters)
            - ``mi`` (miles)
            - ``ft`` (feet)
            - ``nm``, ``nmi`` (nautical miles)

        Some example strings that will work include:

            - ``41.5;-81.0``
            - ``41.5,-81.0``
            - ``41.5 -81.0``
            - ``41.5 N -81.0 W``
            - ``-41.5 S;81.0 E``
            - ``23 26m 22s N 23 27m 30s E``
            - ``23 26' 22" N 23 27' 30" E``
            - ``UT: N 39°20' 0'' / W 74°35' 0''``

        """
        match = re.match(cls.POINT_PATTERN, re.sub(r"''", r'"', string))
        if match:
            latitude_direction = None
            if match.group("latitude_direction_front"):
                latitude_direction = match.group("latitude_direction_front")
            elif match.group("latitude_direction_back"):
                latitude_direction = match.group("latitude_direction_back")

            longitude_direction = None
            if match.group("longitude_direction_front"):
                longitude_direction = match.group("longitude_direction_front")
            elif match.group("longitude_direction_back"):
                longitude_direction = match.group("longitude_direction_back")
            latitude = cls.parse_degrees(
                match.group('latitude_degrees') or 0.0,
                match.group('latitude_arcminutes') or 0.0,
                match.group('latitude_arcseconds') or 0.0,
                latitude_direction
            )
            longitude = cls.parse_degrees(
                match.group('longitude_degrees') or 0.0,
                match.group('longitude_arcminutes') or 0.0,
                match.group('longitude_arcseconds') or 0.0,
                longitude_direction
            )
            altitude = cls.parse_altitude(
                match.group('altitude_distance'),
                match.group('altitude_units')
            )
            return cls(latitude, longitude, altitude)
        else:
            raise ValueError(
                "Failed to create Point instance from string: unknown format."
            )

    @classmethod
    def from_sequence(cls, seq):
        """
        Create and return a new ``Point`` instance from any iterable with 2 to
        3 elements.  The elements, if present, must be latitude, longitude,
        and altitude, respectively.
        """
        args = tuple(islice(seq, 4))
        if len(args) > 3:
            raise ValueError('When creating a Point from sequence, it '
                             'must not have more than 3 items.')
        return cls(*args)

    @classmethod
    def from_point(cls, point):
        """
        Create and return a new ``Point`` instance from another ``Point``
        instance.
        """
        return cls(point.latitude, point.longitude, point.altitude)
