"""
.. versionadded:: 0.93

Geopy can calculate geodesic distance between two points using the
[Vincenty distance](https://en.wikipedia.org/wiki/Vincenty's_formulae) or
[great-circle distance](https://en.wikipedia.org/wiki/Great-circle_distance)
formulas, with a default of Vincenty available as the function
`geopy.distance.distance`.

Great-circle distance (:class:`.great_circle`) uses a spherical model of
the earth, using the mean earth radius as defined by the International
Union of Geodesy and Geophysics, (2*a + b)/3 = 6371.0087714150598
kilometers approx 6371.009 km (for WGS-84), resulting in an error of up
to about 0.5%. The radius value is stored in
:const:`distance.EARTH_RADIUS`, so it can be customized (it should
always be in kilometers, however).

Vincenty distance (:class:`.vincenty`) uses a more accurate ellipsoidal model
of the earth. This is the default distance formula, and is thus aliased as
``distance.distance``. There are multiple popular ellipsoidal models, and
which one will be the most accurate depends on where your points are located
on the earth. The default is the WGS-84 ellipsoid, which is the most globally
accurate. geopy includes a few other
models in the distance.ELLIPSOIDS dictionary::

                  model             major (km)   minor (km)     flattening
    ELLIPSOIDS = {'WGS-84':        (6378.137,    6356.7523142,  1 / \
                                                                298.257223563),
                  'GRS-80':        (6378.137,    6356.7523141,  1 / \
                                                                298.257222101),
                  'Airy (1830)':   (6377.563396, 6356.256909,   1 / \
                                                                299.3249646),
                  'Intl 1924':     (6378.388,    6356.911946,   1 / 297.0),
                  'Clarke (1880)': (6378.249145, 6356.51486955, 1 / 293.465),
                  'GRS-67':        (6378.1600,   6356.774719,   1 / 298.25),
                  }

Here's an example usage of distance.vincenty::

    >>> from geopy.distance import vincenty
    >>> newport_ri = (41.49008, -71.312796)
    >>> cleveland_oh = (41.499498, -81.695391)
    >>> print(vincenty(newport_ri, cleveland_oh).miles)
    538.3904451566326

Using great-circle distance::

    >>> from geopy.distance import great_circle
    >>> newport_ri = (41.49008, -71.312796)
    >>> cleveland_oh = (41.499498, -81.695391)
    >>> print(great_circle(newport_ri, cleveland_oh).miles)
    537.1485284062816

You can change the ellipsoid model used by the Vincenty formula like so::

    >>> distance.vincenty(ne, cl, ellipsoid='GRS-80').miles

The above model name will automatically be retrieved from the
ELLIPSOIDS dictionary. Alternatively, you can specify the model values
directly::

    >>> distance.vincenty(ne, cl, ellipsoid=(6377., 6356., 1 / 297.)).miles

Distances support simple arithmetic, making it easy to do things like
calculate the length of a path::

    >>> d = distance.distance
    >>> _, wa = g.geocode('Washington, DC')
    >>> _, pa = g.geocode('Palo Alto, CA')
    >>> print((d(ne, cl) + d(cl, wa) + d(wa, pa)).miles)
    3276.157156868931

"""
from __future__ import division

from math import atan, tan, sin, cos, pi, sqrt, atan2, asin
from geopy.units import radians
from geopy import units, util
from geopy.point import Point
from geopy.compat import string_compare

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

class Distance(object):
    """
    Base for :class:`.great_circle` and :class:`.vincenty`.
    """

    def __init__(self, *args, **kwargs):
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
        """
        Abstract method for measure
        """
        raise NotImplementedError()

    def __repr__(self): # pragma: no cover
        return 'Distance(%s)' % self.kilometers

    def __str__(self): # pragma: no cover
        return '%s km' % self.__kilometers

    def __cmp__(self, other):
        if isinstance(other, Distance):
            return cmp(self.kilometers, other.kilometers)
        else:
            return cmp(self.kilometers, other)

    @property
    def kilometers(self): # pylint: disable=C0111
        return self.__kilometers

    @property
    def km(self): # pylint: disable=C0111
        return self.kilometers

    @property
    def meters(self): # pylint: disable=C0111
        return units.meters(kilometers=self.kilometers)

    @property
    def m(self): # pylint: disable=C0111
        return self.meters

    @property
    def miles(self): # pylint: disable=C0111
        return units.miles(kilometers=self.kilometers)

    @property
    def mi(self): # pylint: disable=C0111
        return self.miles

    @property
    def feet(self): # pylint: disable=C0111
        return units.feet(kilometers=self.kilometers)

    @property
    def ft(self): # pylint: disable=C0111
        return self.feet

    @property
    def nautical(self): # pylint: disable=C0111
        return units.nautical(kilometers=self.kilometers)

    @property
    def nm(self): # pylint: disable=C0111
        return self.nautical


class great_circle(Distance):
    """
    Use spherical geometry to calculate the surface distance between two
    geodesic points. This formula can be written many different ways,
    including just the use of the spherical law of cosines or the haversine
    formula.

    Set which radius of the earth to use by specifying a 'radius' keyword
    argument. It must be in kilometers. The default is to use the module
    constant `EARTH_RADIUS`, which uses the average great-circle radius.

    Example::

        >>> from geopy.distance import great_circle
        >>> newport_ri = (41.49008, -71.312796)
        >>> cleveland_oh = (41.499498, -81.695391)
        >>> great_circle(newport_ri, cleveland_oh).miles
        537.1485284062816

    """

    def __init__(self, *args, **kwargs):
        self.RADIUS = kwargs.pop('radius', EARTH_RADIUS)
        super(great_circle, self).__init__(*args, **kwargs)

    def measure(self, a, b):
        a, b = Point(a), Point(b)

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

    def destination(self, point, bearing, distance=None): # pylint: disable=W0621
        """
        TODO docs.
        """
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


class vincenty(Distance):
    """
    Calculate the geodesic distance between two points using the formula
    devised by Thaddeus Vincenty, with an accurate ellipsoidal model of the
    earth.

    Set which ellipsoidal model of the earth to use by specifying an
    ``ellipsoid`` keyword argument. The default is 'WGS-84', which is the
    most globally accurate model.  If ``ellipsoid`` is a string, it is
    looked up in the `ELLIPSOIDS` dictionary to obtain the major and minor
    semiaxes and the flattening. Otherwise, it should be a tuple with those
    values.  See the comments above the `ELLIPSOIDS` dictionary for
    more information.

    Example::

        >>> from geopy.distance import vincenty
        >>> newport_ri = (41.49008, -71.312796)
        >>> cleveland_oh = (41.499498, -81.695391)
        >>> print(vincenty(newport_ri, cleveland_oh).miles)
        538.3904451566326

    Note: This implementation of Vincenty distance fails to converge for
    some valid points. In some cases, a result can be obtained by increasing
    the number of iterations (`iterations` keyword argument, given in the
    class `__init__`, with a default of 20). It may be preferable to use
    :class:`.great_circle`, which is marginally less accurate, but always
    produces a result.
    """

    ellipsoid_key = None
    ELLIPSOID = None

    def __init__(self, *args, **kwargs):
        self.set_ellipsoid(kwargs.pop('ellipsoid', 'WGS-84'))
        self.iterations = kwargs.pop('iterations', 20)
        major, minor, f = self.ELLIPSOID # pylint: disable=W0612
        super(vincenty, self).__init__(*args, **kwargs)

    def set_ellipsoid(self, ellipsoid):
        """
        Change the ellipsoid used in the calculation.
        """
        if not isinstance(ellipsoid, (list, tuple)):
            try:
                self.ELLIPSOID = ELLIPSOIDS[ellipsoid]
                self.ellipsoid_key = ellipsoid
            except KeyError:
                raise Exception(
                    "Invalid ellipsoid. See geopy.distance.ELIPSOIDS"
                )
        else:
            self.ELLIPSOID = ellipsoid
            self.ellipsoid_key = None
        return

    def measure(self, a, b):
        a, b = Point(a), Point(b)
        lat1, lng1 = radians(degrees=a.latitude), radians(degrees=a.longitude)
        lat2, lng2 = radians(degrees=b.latitude), radians(degrees=b.longitude)

        if isinstance(self.ELLIPSOID, string_compare):
            major, minor, f = ELLIPSOIDS[self.ELLIPSOID]
        else:
            major, minor, f = self.ELLIPSOID

        delta_lng = lng2 - lng1

        reduced_lat1 = atan((1 - f) * tan(lat1))
        reduced_lat2 = atan((1 - f) * tan(lat2))

        sin_reduced1, cos_reduced1 = sin(reduced_lat1), cos(reduced_lat1)
        sin_reduced2, cos_reduced2 = sin(reduced_lat2), cos(reduced_lat2)

        lambda_lng = delta_lng
        lambda_prime = 2 * pi

        iter_limit = self.iterations

        i = 0
        while abs(lambda_lng - lambda_prime) > 10e-12 and i <= iter_limit:
            i += 1

            sin_lambda_lng, cos_lambda_lng = sin(lambda_lng), cos(lambda_lng)

            sin_sigma = sqrt(
                (cos_reduced2 * sin_lambda_lng) ** 2 +
                (cos_reduced1 * sin_reduced2 -
                 sin_reduced1 * cos_reduced2 * cos_lambda_lng) ** 2
            )

            if sin_sigma == 0:
                return 0 # Coincident points

            cos_sigma = (
                sin_reduced1 * sin_reduced2 +
                cos_reduced1 * cos_reduced2 * cos_lambda_lng
            )

            sigma = atan2(sin_sigma, cos_sigma)

            sin_alpha = (
                cos_reduced1 * cos_reduced2 * sin_lambda_lng / sin_sigma
            )
            cos_sq_alpha = 1 - sin_alpha ** 2

            if cos_sq_alpha != 0:
                cos2_sigma_m = cos_sigma - 2 * (
                    sin_reduced1 * sin_reduced2 / cos_sq_alpha
                )
            else:
                cos2_sigma_m = 0.0 # Equatorial line

            C = f / 16. * cos_sq_alpha * (4 + f * (4 - 3 * cos_sq_alpha))

            lambda_prime = lambda_lng
            lambda_lng = (
                delta_lng + (1 - C) * f * sin_alpha * (
                    sigma + C * sin_sigma * (
                        cos2_sigma_m + C * cos_sigma * (
                            -1 + 2 * cos2_sigma_m ** 2
                        )
                    )
                )
            )

        if i > iter_limit:
            raise ValueError("Vincenty formula failed to converge!")

        u_sq = cos_sq_alpha * (major ** 2 - minor ** 2) / minor ** 2

        A = 1 + u_sq / 16384. * (
            4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq))
        )

        B = u_sq / 1024. * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))

        delta_sigma = (
            B * sin_sigma * (
                cos2_sigma_m + B / 4. * (
                    cos_sigma * (
                        -1 + 2 * cos2_sigma_m ** 2
                    ) - B / 6. * cos2_sigma_m * (
                        -3 + 4 * sin_sigma ** 2
                    ) * (
                        -3 + 4 * cos2_sigma_m ** 2
                    )
                )
            )
        )

        s = minor * A * (sigma - delta_sigma)
        return s

    def destination(self, point, bearing, distance=None): # pylint: disable=W0621
        """
        TODO docs.
        """
        point = Point(point)
        lat1 = units.radians(degrees=point.latitude)
        lng1 = units.radians(degrees=point.longitude)
        bearing = units.radians(degrees=bearing)

        if distance is None:
            distance = self
        if isinstance(distance, Distance):
            distance = distance.kilometers

        ellipsoid = self.ELLIPSOID
        if isinstance(ellipsoid, string_compare):
            ellipsoid = ELLIPSOIDS[ellipsoid]

        major, minor, f = ellipsoid

        tan_reduced1 = (1 - f) * tan(lat1)
        cos_reduced1 = 1 / sqrt(1 + tan_reduced1 ** 2)
        sin_reduced1 = tan_reduced1 * cos_reduced1
        sin_bearing, cos_bearing = sin(bearing), cos(bearing)
        sigma1 = atan2(tan_reduced1, cos_bearing)
        sin_alpha = cos_reduced1 * sin_bearing
        cos_sq_alpha = 1 - sin_alpha ** 2
        u_sq = cos_sq_alpha * (major ** 2 - minor ** 2) / minor ** 2

        A = 1 + u_sq / 16384. * (
            4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq))
        )
        B = u_sq / 1024. * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))

        sigma = distance / (minor * A)
        sigma_prime = 2 * pi

        while abs(sigma - sigma_prime) > 10e-12:
            cos2_sigma_m = cos(2 * sigma1 + sigma)
            sin_sigma, cos_sigma = sin(sigma), cos(sigma)
            delta_sigma = B * sin_sigma * (
                cos2_sigma_m + B / 4. * (
                    cos_sigma * (
                        -1 + 2 * cos2_sigma_m
                    ) - B / 6. * cos2_sigma_m * (
                        -3 + 4 * sin_sigma ** 2
                    ) * (
                        -3 + 4 * cos2_sigma_m ** 2
                    )
                )
            )
            sigma_prime = sigma
            sigma = distance / (minor * A) + delta_sigma

        sin_sigma, cos_sigma = sin(sigma), cos(sigma)

        lat2 = atan2(
            sin_reduced1 * cos_sigma + cos_reduced1 * sin_sigma * cos_bearing,
            (1 - f) * sqrt(
                sin_alpha ** 2 + (
                    sin_reduced1 * sin_sigma -
                    cos_reduced1 * cos_sigma * cos_bearing
                ) ** 2
            )
        )

        lambda_lng = atan2(
            sin_sigma * sin_bearing,
            cos_reduced1 * cos_sigma - sin_reduced1 * sin_sigma * cos_bearing
        )

        C = f / 16. * cos_sq_alpha * (4 + f * (4 - 3 * cos_sq_alpha))

        delta_lng = (
            lambda_lng - (1 - C) * f * sin_alpha * (
                sigma + C * sin_sigma * (
                    cos2_sigma_m + C * cos_sigma * (
                        -1 + 2 * cos2_sigma_m ** 2
                    )
                )
            )
        )

        lng2 = lng1 + delta_lng

        return Point(units.degrees(radians=lat2), units.degrees(radians=lng2))


# Set the default distance formula to the most generally accurate.

distance = VincentyDistance = vincenty
GreatCircleDistance = great_circle
