import re
from itertools import islice
from geopy import util, units, format

class Point(object):
    """
    A geodetic point with latitude, longitude, and altitude.
    
    Latitude and longitude are floating point values in degrees.
    Altitude is a floating point value in kilometers. The reference level
    is never considered and is thus application dependent, so be consistent!
    The default for all values is 0.
    
    Points can be created in a number of ways...
        
    With longitude, latitude, and altitude:
    >>> p1 = Point(41.5, -81, 0)
    >>> p2 = Point(latitude=41.5, longitude=-81)
    
    With a sequence of 0 to 3 values (longitude, latitude, altitude):
    >>> p1 = Point([41.5, -81, 0])
    >>> p2 = Point((41.5, -81))
    
    Copy another `Point` instance:
    >>> p2 = Point(p1)
    >>> p2 == p1
    True
    >>> p2 is p1
    False
    
    Give an object with a 'point' attribute, such as a `Location` instance:
    >>> p = Point(location)
    
    Give a string containing at least latitude and longitude:
    >>> p1 = Point('41.5,-81.0')
    >>> p2 = Point('41.5 N -81.0 W')
    >>> p3 = Point('-41.5 S, 81.0 E, 2.5km')
    >>> p4 = Point('23 26m 22s N 23 27m 30s E 21.0mi')
    >>> p5 = Point('''3 26' 22" N 23 27' 30" E''')
    
    Point values can be accessed by name or by index:
    >>> p = Point(41.5, -81.0, 0)
    >>> p.latitude == p[0]
    True
    >>> p.longitude == p[1]
    True
    >>> p.altitude == p[2]
    True
    
    When unpacking (or iterating), only latitude and longitude are included:
    >>> latitude, longitude = p
    
    """
    UTIL_PATTERNS = dict(
        FLOAT=r'\d+(?:\.\d+)?',
        DEGREE=format.DEGREE,
        PRIME=format.PRIME,
        DOUBLE_PRIME=format.DOUBLE_PRIME,
        SEP=r'\s*[,;\s]\s*'
    )
    POINT_PATTERN = re.compile(r"""
        \s*
        (?P<latitude>
          (?P<latitude_degrees>-?%(FLOAT)s)(?:[%(DEGREE)s ][ ]*
            (?:(?P<latitude_arcminutes>%(FLOAT)s)[%(PRIME)s'm][ ]*)?
            (?:(?P<latitude_arcseconds>%(FLOAT)s)[%(DOUBLE_PRIME)s"s][ ]*)?
            )?(?P<latitude_direction>[NS])?)
        %(SEP)s
        (?P<longitude>
          (?P<longitude_degrees>-?%(FLOAT)s)(?:[%(DEGREE)s\s][ ]*
          (?:(?P<longitude_arcminutes>%(FLOAT)s)[%(PRIME)s'm][ ]*)?
          (?:(?P<longitude_arcseconds>%(FLOAT)s)[%(DOUBLE_PRIME)s"s][ ]*)?
          )?(?P<longitude_direction>[EW])?)(?:
        %(SEP)s
          (?P<altitude>
            (?P<altitude_distance>-?%(FLOAT)s)[ ]*
            (?P<altitude_units>km|m|mi|ft|nm|nmi)))?
        \s*$
    """ % UTIL_PATTERNS, re.X)
    
    def __new__(cls, latitude=None, longitude=None, altitude=None):
        single_arg = longitude is None and altitude is None
        if single_arg and not isinstance(latitude, util.NUMBER_TYPES):
            arg = latitude
            if arg is None:
                pass
            elif isinstance(arg, Point):
                return cls.from_point(arg)
            elif isinstance(arg, basestring):
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
        
        latitude = float(latitude or 0)
        if abs(latitude) > 90:
            raise ValueError("Latitude out of range [-90, 90]: %r" % latitude)
        
        longitude = float(longitude or 0)
        if abs(longitude) > 180:
            raise ValueError("Longitude out of range [-180, 180]: %r" % longitude)
        
        altitude = float(altitude or 0)
        
        self = super(Point, cls).__new__(cls)
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        return self
    
    def __getitem__(self, index):
        return (self.latitude, self.longitude, self.altitude)[index]
    
    def __setitem__(self, index, value):
        point = [self.latitude, self.longitude, self.altitude]
        point[index] = value
        self.latitude, self.longitude, self.altitude = point
    
    def __iter__(self):
        return iter((self.latitude, self.longitude, self.altitude))
    
    def __repr__(self):
        return "Point(%r, %r, %r)" % (
            self.latitude, self.longitude, self.altitude
        )
    
    def format(self, altitude=None, deg_char='', min_char='m', sec_char='s'):
        latitude = "%s %s" % (
            format.angle(abs(self.latitude), deg_char, min_char, sec_char),
            self.latitude >= 0 and 'N' or 'S'
        )
        longitude = "%s %s" % (
            format.angle(abs(self.longitude), deg_char, min_char, sec_char),
            self.longitude >= 0 and 'E' or 'W'
        )
        coordinates = [latitude, longitude]
        
        if altitude is None:
            altitude = bool(self.altitude)
        if altitude:
            if not isinstance(altitude, basestring):
                altitude = 'km'
            coordinates.append(self.format_altitude(altitude))
        
        return ", ".join(coordinates)
    
    def format_decimal(self, altitude=None):
        latitude = "%s" % self.latitude
        longitude = "%s" % self.longitude
        coordinates = [latitude, longitude]
        
        if altitude is None:
            altitude = bool(self.altitude)
        if altitude:
            if not isinstance(altitude, basestring):
                altitude = 'km'
            coordinates.append(self.format_altitude(altitude))
        
        return ", ".join(coordinates)
    
    def format_altitude(self, unit='km'):
        return format.distance(self.altitude, unit)
    
    def __str__(self):
        return self.format()
    
    def __unicode__(self):
        return self.format(
            None, format.DEGREE, format.PRIME, format.DOUBLE_PRIME
        )
    
    def __eq__(self, other):
        return tuple(self) == tuple(other)
    
    def __ne__(self, other):
        return tuple(self) != tuple(other)
    
    @classmethod
    def parse_degrees(cls, degrees, arcminutes, arcseconds, direction=None):
        negative = degrees < 0 or degrees.startswith('-')
        degrees = float(degrees or 0)
        arcminutes = float(arcminutes or 0)
        arcseconds = float(arcseconds or 0)
        
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
            return CONVERTERS[unit](distance)
        else:
            return distance
    
    @classmethod
    def from_string(cls, string):
        """
        Create and return a Point instance from a string containing latitude
        and longitude, and optionally, altitude.
        
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
        
            km (kilometers)
            m (meters)
            mi (miles)
            ft (feet)
            nm, nmi (nautical miles)
        
        Some example strings the will work include:
        
            41.5;-81.0
            41.5,-81.0
            41.5 -81.0
            41.5 N -81.0 W
            -41.5 S;81.0 E
            23 26m 22s N 23 27m 30s E
            23 26' 22" N 23 27' 30" E
        
        """
        match = re.match(cls.POINT_PATTERN, string)
        if match:
            latitude = cls.parse_degrees(
                match.group('latitude_degrees'),
                match.group('latitude_arcminutes'),
                match.group('latitude_arcseconds'),
                match.group('latitude_direction')
            )
            longitude = cls.parse_degrees(
                match.group('longitude_degrees'),
                match.group('longitude_arcminutes'),
                match.group('longitude_arcseconds'),
                match.group('longitude_direction'),
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
        Create and return a new Point instance from any iterable with 0 to
        3 elements.  The elements, if present, must be latitude, longitude,
        and altitude, respectively.
        
        """
        args = tuple(islice(seq, 4))
        return cls(*args)
    
    @classmethod
    def from_point(cls, point):
        """
        Create and return a new Point instance from another Point instance.
        
        """
        return cls(point.latitude, point.longitude, point.altitude)
