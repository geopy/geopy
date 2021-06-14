"""
Geopy can calculate geodesic distance between two points using the
`geodesic distance
<https://en.wikipedia.org/wiki/Geodesics_on_an_ellipsoid>`_ or the
`great-circle distance
<https://en.wikipedia.org/wiki/Great-circle_distance>`_,
with a default of the geodesic distance available as the function
``geopy.distance.distance``.

Great-circle distance (:class:`.great_circle`) uses a spherical model of
the earth, using the mean earth radius as defined by the International
Union of Geodesy and Geophysics, (2\\ *a* + *b*)/3 = 6371.0087714150598
kilometers approx 6371.009 km (for WGS-84), resulting in an error of up
to about 0.5%. The radius value is stored in
:const:`distance.EARTH_RADIUS`, so it can be customized (it should
always be in kilometers, however).

The geodesic distance is the shortest distance on the surface of an
ellipsoidal model of the earth.  The default algorithm uses the method
is given by `Karney (2013)
<https://doi.org/10.1007%2Fs00190-012-0578-z>`_ (:class:`.geodesic`);
this is accurate to round-off and always converges.

``geopy.distance.distance`` currently uses :class:`.geodesic`.

There are multiple popular ellipsoidal models,
and which one will be the most accurate depends on where your points are
located on the earth.  The default is the WGS-84 ellipsoid, which is the
most globally accurate.  geopy includes a few other models in the
:const:`distance.ELLIPSOIDS` dictionary::

                  model             major (km)   minor (km)     flattening
    ELLIPSOIDS = {'WGS-84':        (6378.137,    6356.7523142,  1 / 298.257223563),
                  'GRS-80':        (6378.137,    6356.7523141,  1 / 298.257222101),
                  'Airy (1830)':   (6377.563396, 6356.256909,   1 / 299.3249646),
                  'Intl 1924':     (6378.388,    6356.911946,   1 / 297.0),
                  'Clarke (1880)': (6378.249145, 6356.51486955, 1 / 293.465),
                  'GRS-67':        (6378.1600,   6356.774719,   1 / 298.25),
                  }

Here are examples of ``distance.distance`` usage, taking pair
of :code:`(lat, lon)` tuples::

    >>> from geopy import distance
    >>> newport_ri = (41.49008, -71.312796)
    >>> cleveland_oh = (41.499498, -81.695391)
    >>> print(distance.distance(newport_ri, cleveland_oh).miles)
    538.39044536

    >>> wellington = (-41.32, 174.81)
    >>> salamanca = (40.96, -5.50)
    >>> print(distance.distance(wellington, salamanca).km)
    19959.6792674

Using :class:`.great_circle` distance::

    >>> print(distance.great_circle(newport_ri, cleveland_oh).miles)
    536.997990696

You can change the ellipsoid model used by the geodesic formulas like so::

    >>> ne, cl = newport_ri, cleveland_oh
    >>> print(distance.geodesic(ne, cl, ellipsoid='GRS-80').miles)

The above model name will automatically be retrieved from the
:const:`distance.ELLIPSOIDS` dictionary. Alternatively, you can specify
the model values directly::

    >>> distance.geodesic(ne, cl, ellipsoid=(6377., 6356., 1 / 297.)).miles

Distances support simple arithmetic, making it easy to do things like
calculate the length of a path::

    >>> from geopy import Nominatim
    >>> d = distance.distance
    >>> g = Nominatim(user_agent="specify_your_app_name_here")
    >>> _, wa = g.geocode('Washington, DC')
    >>> _, pa = g.geocode('Palo Alto, CA')
    >>> print((d(ne, cl) + d(cl, wa) + d(wa, pa)).miles)
    3277.30439191


.. _distance_altitudes:

Currently all algorithms assume that altitudes of the points are either
zero (as in the examples above) or equal, and are relatively small.
Thus altitudes never affect the resulting distances::

    >>> from geopy import distance
    >>> newport_ri = (41.49008, -71.312796)
    >>> cleveland_oh = (41.499498, -81.695391)
    >>> print(distance.distance(newport_ri, cleveland_oh).km)
    866.4554329098687
    >>> newport_ri = (41.49008, -71.312796, 100)
    >>> cleveland_oh = (41.499498, -81.695391, 100)
    >>> print(distance.distance(newport_ri, cleveland_oh).km)
    866.4554329098687

If you need to calculate distances with elevation, then for short
distances the `Euclidean distance
<https://en.wikipedia.org/wiki/Euclidean_distance>`_ formula might give
a suitable approximation::

    >>> import math
    >>> from geopy import distance
    >>> p1 = (43.668613, 40.258916, 0.976)
    >>> p2 = (43.658852, 40.250839, 1.475)
    >>> flat_distance = distance.distance(p1[:2], p2[:2]).km
    >>> print(flat_distance)
    1.265133525952866
    >>> euclidian_distance = math.sqrt(flat_distance**2 + (p2[2] - p1[2])**2)
    >>> print(euclidian_distance)
    1.359986705262199

An attempt to calculate distances between points with different altitudes
would result in a :class:`ValueError` exception.

"""
from math import asin, atan2, cos, sin, sqrt

from geographiclib.geodesic import Geodesic

from geopy import units, util
from geopy.point import Point
from geopy.units import radians

# IUGG mean earth radius in kilometers, from
# https://en.wikipedia.org/wiki/Earth_radius#Mean_radius.  Using a
# sphere with this radius results in an error of up to about 0.5%.
EARTH_RADIUS = 6371.009

# From http://www.movable-type.co.uk/scripts/LatLongVincenty.html:
#   The most accurate and widely used globally-applicable model for the earth
#   ellipsoid is WGS-84, used in this script. Other ellipsoids offering a
#   better fit to the local geoid include Airy (1830) in the UK, International
#   1924 in much of Europe, Clarke (1880) in Africa, and GRS-67 in South
#   America. America (NAD83) and Australia (GDA) use GRS-80, functionally
#   equivalent to the WGS-84 ellipsoid.
ELLIPSOIDS = {
    # model           major (km)   minor (km)     flattening
    'WGS-84':        (6378.137, 6356.7523142, 1 / 298.257223563),
    'GRS-80':        (6378.137, 6356.7523141, 1 / 298.257222101),
    'Airy (1830)':   (6377.563396, 6356.256909, 1 / 299.3249646),
    'Intl 1924':     (6378.388, 6356.911946, 1 / 297.0),
    'Clarke (1880)': (6378.249145, 6356.51486955, 1 / 293.465),
    'GRS-67':        (6378.1600, 6356.774719, 1 / 298.25)
}


def cmp(a, b):
    return (a > b) - (a < b)


def lonlat(x, y, z=0):
    """
    ``geopy.distance.distance`` accepts coordinates in ``(y, x)``/``(lat, lon)``
    order, while some other libraries and systems might use
    ``(x, y)``/``(lon, lat)``.

    This function provides a convenient way to convert coordinates of the
    ``(x, y)``/``(lon, lat)`` format to a :class:`geopy.point.Point` instance.

    Example::

        >>> from geopy.distance import lonlat, distance
        >>> newport_ri_xy = (-71.312796, 41.49008)
        >>> cleveland_oh_xy = (-81.695391, 41.499498)
        >>> print(distance(lonlat(*newport_ri_xy), lonlat(*cleveland_oh_xy)).miles)
        538.3904453677203

    :param x: longitude
    :param y: latitude
    :param z: (optional) altitude
    :return: Point(latitude, longitude, altitude)
    """
    return Point(y, x, z)


def _ensure_same_altitude(a, b):
    if abs(a.altitude - b.altitude) > 1e-6:
        raise ValueError(
            'Calculating distance between points with different altitudes '
            'is not supported'
        )
    # Note: non-zero equal altitudes are fine: assuming that
    # the elevation is many times smaller than the Earth radius
    # it won't give much error.


class Distance:
    """
    Base class for other distance algorithms. Represents a distance.

    Can be used for units conversion::

        >>> from geopy.distance import Distance
        >>> Distance(miles=10).km
        16.09344

    Distance instances have all *distance* properties from :mod:`geopy.units`,
    e.g.: ``km``, ``m``, ``meters``, ``miles`` and so on.

    Distance instances are immutable.

    They support comparison::

        >>> from geopy.distance import Distance
        >>> Distance(kilometers=2) == Distance(meters=2000)
        True
        >>> Distance(kilometers=2) > Distance(miles=1)
        True

    String representation::

        >>> from geopy.distance import Distance
        >>> repr(Distance(kilometers=2))
        'Distance(2.0)'
        >>> str(Distance(kilometers=2))
        '2.0 km'
        >>> repr(Distance(miles=2))
        'Distance(3.218688)'
        >>> str(Distance(miles=2))
        '3.218688 km'

    Arithmetics::

        >>> from geopy.distance import Distance
        >>> -Distance(miles=2)
        Distance(-3.218688)
        >>> Distance(miles=2) + Distance(kilometers=1)
        Distance(4.218688)
        >>> Distance(miles=2) - Distance(kilometers=1)
        Distance(2.218688)
        >>> Distance(kilometers=6) * 5
        Distance(30.0)
        >>> Distance(kilometers=6) / 5
        Distance(1.2)
    """

    def __init__(self, *args, **kwargs):
        """
        There are 3 ways to create a distance:

        - From kilometers::

            >>> from geopy.distance import Distance
            >>> Distance(1.42)
            Distance(1.42)

        - From units::

            >>> from geopy.distance import Distance
            >>> Distance(kilometers=1.42)
            Distance(1.42)
            >>> Distance(miles=1)
            Distance(1.609344)

        - From points (for non-abstract distances only),
          calculated as a sum of distances between all points::

            >>> from geopy.distance import geodesic
            >>> geodesic((40, 160), (40.1, 160.1))
            Distance(14.003702498106215)
            >>> geodesic((40, 160), (40.1, 160.1), (40.2, 160.2))
            Distance(27.999954644813478)
        """

        kilometers = kwargs.pop('kilometers', 0)
        if len(args) == 1:
            # if we only get one argument we assume
            # it's a known distance instead of
            # calculating it first
            kilometers += args[0]
        elif len(args) > 1:
            for a, b in util.pairwise(args):
                kilometers += self.measure(a, b)

        kilometers += units.kilometers(**kwargs)
        self.__kilometers = kilometers

    def __add__(self, other):
        if isinstance(other, Distance):
            return self.__class__(self.kilometers + other.kilometers)
        else:
            raise TypeError(
                "Distance instance must be added with Distance instance."
            )

    def __neg__(self):
        return self.__class__(-self.kilometers)

    def __sub__(self, other):
        return self + -other

    def __mul__(self, other):
        return self.__class__(self.kilometers * other)

    def __div__(self, other):
        if isinstance(other, Distance):
            return self.kilometers / other.kilometers
        else:
            return self.__class__(self.kilometers / other)

    __truediv__ = __div__

    def __abs__(self):
        return self.__class__(abs(self.kilometers))

    def __nonzero__(self):
        return bool(self.kilometers)

    __bool__ = __nonzero__

    def measure(self, a, b):
        # Intentionally not documented, because this method is not supposed
        # to be used directly.
        raise NotImplementedError("Distance is an abstract class")

    def destination(self, point, bearing, distance=None):
        """
        Calculate destination point using a starting point, bearing
        and a distance. This method works for non-abstract distances only.

        Example: a point 10 miles east from ``(34, 148)``::

            >>> import geopy.distance
            >>> geopy.distance.distance(miles=10).destination((34, 148), bearing=90)
            Point(33.99987666492774, 148.17419994321995, 0.0)

        :param point: Starting point.
        :type point: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param float bearing: Bearing in degrees: 0 -- North, 90 -- East,
            180 -- South, 270 or -90 -- West.

        :param distance: Distance, can be used to override
            this instance::

                >>> from geopy.distance import distance, Distance
                >>> distance(miles=10).destination((34, 148), bearing=90, \
distance=Distance(100))
                Point(33.995238229104764, 149.08238904409637, 0.0)

        :type distance: :class:`.Distance`

        :rtype: :class:`geopy.point.Point`
        """
        raise NotImplementedError("Distance is an abstract class")

    def __repr__(self):  # pragma: no cover
        return 'Distance(%s)' % self.kilometers

    def __str__(self):  # pragma: no cover
        return '%s km' % self.__kilometers

    def __cmp__(self, other):  # py2 only
        if isinstance(other, Distance):
            return cmp(self.kilometers, other.kilometers)
        else:
            return cmp(self.kilometers, other)

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    @property
    def feet(self):
        return units.feet(kilometers=self.kilometers)

    @property
    def ft(self):
        return self.feet

    @property
    def kilometers(self):
        return self.__kilometers

    @property
    def km(self):
        return self.kilometers

    @property
    def m(self):
        return self.meters

    @property
    def meters(self):
        return units.meters(kilometers=self.kilometers)

    @property
    def mi(self):
        return self.miles

    @property
    def miles(self):
        return units.miles(kilometers=self.kilometers)

    @property
    def nautical(self):
        return units.nautical(kilometers=self.kilometers)

    @property
    def nm(self):
        return self.nautical


class great_circle(Distance):
    """
    Use spherical geometry to calculate the surface distance between
    points.

    Set which radius of the earth to use by specifying a ``radius`` keyword
    argument. It must be in kilometers. The default is to use the module
    constant `EARTH_RADIUS`, which uses the average great-circle radius.

    Example::

        >>> from geopy.distance import great_circle
        >>> newport_ri = (41.49008, -71.312796)
        >>> cleveland_oh = (41.499498, -81.695391)
        >>> print(great_circle(newport_ri, cleveland_oh).miles)
        536.997990696

    """

    def __init__(self, *args, **kwargs):
        self.RADIUS = kwargs.pop('radius', EARTH_RADIUS)
        super().__init__(*args, **kwargs)

    def measure(self, a, b):
        a, b = Point(a), Point(b)
        _ensure_same_altitude(a, b)

        lat1, lng1 = radians(degrees=a.latitude), radians(degrees=a.longitude)
        lat2, lng2 = radians(degrees=b.latitude), radians(degrees=b.longitude)

        sin_lat1, cos_lat1 = sin(lat1), cos(lat1)
        sin_lat2, cos_lat2 = sin(lat2), cos(lat2)

        delta_lng = lng2 - lng1
        cos_delta_lng, sin_delta_lng = cos(delta_lng), sin(delta_lng)

        d = atan2(sqrt((cos_lat2 * sin_delta_lng) ** 2 +
                       (cos_lat1 * sin_lat2 -
                        sin_lat1 * cos_lat2 * cos_delta_lng) ** 2),
                  sin_lat1 * sin_lat2 + cos_lat1 * cos_lat2 * cos_delta_lng)

        return self.RADIUS * d

    def destination(self, point, bearing, distance=None):
        point = Point(point)
        lat1 = units.radians(degrees=point.latitude)
        lng1 = units.radians(degrees=point.longitude)
        bearing = units.radians(degrees=bearing)

        if distance is None:
            distance = self
        if isinstance(distance, Distance):
            distance = distance.kilometers

        d_div_r = float(distance) / self.RADIUS

        lat2 = asin(
            sin(lat1) * cos(d_div_r) +
            cos(lat1) * sin(d_div_r) * cos(bearing)
        )

        lng2 = lng1 + atan2(
            sin(bearing) * sin(d_div_r) * cos(lat1),
            cos(d_div_r) - sin(lat1) * sin(lat2)
        )

        return Point(units.degrees(radians=lat2), units.degrees(radians=lng2))


GreatCircleDistance = great_circle


class geodesic(Distance):
    """
    Calculate the geodesic distance between points.

    Set which ellipsoidal model of the earth to use by specifying an
    ``ellipsoid`` keyword argument. The default is 'WGS-84', which is the
    most globally accurate model.  If ``ellipsoid`` is a string, it is
    looked up in the `ELLIPSOIDS` dictionary to obtain the major and minor
    semiaxes and the flattening. Otherwise, it should be a tuple with those
    values.  See the comments above the `ELLIPSOIDS` dictionary for
    more information.

    Example::

        >>> from geopy.distance import geodesic
        >>> newport_ri = (41.49008, -71.312796)
        >>> cleveland_oh = (41.499498, -81.695391)
        >>> print(geodesic(newport_ri, cleveland_oh).miles)
        538.390445368

    """

    def __init__(self, *args, **kwargs):
        self.ellipsoid_key = None
        self.ELLIPSOID = None
        self.geod = None
        self.set_ellipsoid(kwargs.pop('ellipsoid', 'WGS-84'))
        major, minor, f = self.ELLIPSOID
        super().__init__(*args, **kwargs)

    def set_ellipsoid(self, ellipsoid):
        if isinstance(ellipsoid, str):
            try:
                self.ELLIPSOID = ELLIPSOIDS[ellipsoid]
                self.ellipsoid_key = ellipsoid
            except KeyError:
                raise Exception(
                    "Invalid ellipsoid. See geopy.distance.ELLIPSOIDS"
                )
        else:
            self.ELLIPSOID = ellipsoid
            self.ellipsoid_key = None

    def measure(self, a, b):
        a, b = Point(a), Point(b)
        _ensure_same_altitude(a, b)
        lat1, lon1 = a.latitude, a.longitude
        lat2, lon2 = b.latitude, b.longitude

        if not (isinstance(self.geod, Geodesic) and
                self.geod.a == self.ELLIPSOID[0] and
                self.geod.f == self.ELLIPSOID[2]):
            self.geod = Geodesic(self.ELLIPSOID[0], self.ELLIPSOID[2])

        s12 = self.geod.Inverse(lat1, lon1, lat2, lon2,
                                Geodesic.DISTANCE)['s12']

        return s12

    def destination(self, point, bearing, distance=None):
        point = Point(point)
        lat1 = point.latitude
        lon1 = point.longitude
        azi1 = bearing

        if distance is None:
            distance = self
        if isinstance(distance, Distance):
            distance = distance.kilometers

        if not (isinstance(self.geod, Geodesic) and
                self.geod.a == self.ELLIPSOID[0] and
                self.geod.f == self.ELLIPSOID[2]):
            self.geod = Geodesic(self.ELLIPSOID[0], self.ELLIPSOID[2])

        r = self.geod.Direct(lat1, lon1, azi1, distance,
                             Geodesic.LATITUDE | Geodesic.LONGITUDE)

        return Point(r['lat2'], r['lon2'])


GeodesicDistance = geodesic

# Set the default distance formula
distance = GeodesicDistance
