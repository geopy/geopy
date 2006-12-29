from math import *
import util

# Average great-circle radius in kilometers, from Wikipedia.
# Using a sphere with this radius results in an error of up to about 0.5%.
EARTH_RADIUS = 6372.795

# From http://www.movable-type.co.uk/scripts/LatLongVincenty.html:
#   The most accurate and widely used globally-applicable model for the earth
#   ellipsoid is WGS-84, used in this script. Other ellipsoids offering a
#   better fit to the local geoid include Airy (1830) in the UK, International
#   1924 in much of Europe, Clarke (1880) in Africa, and GRS-67 in South
#   America. America (NAD83) and Australia (GDA) use GRS-80, functionally
#   equivalent to the WGS-84 ellipsoid.
#
#             model             major (km)   minor (km)     flattening
ELLIPSOIDS = {'WGS-84':        (6378.137,    6356.7523142,  1 / 298.257223563),
              'GRS-80':        (6378.137,    6356.7523141,  1 / 298.257222101),
              'Airy (1830)':   (6377.563396, 6356.256909,   1 / 299.3249646),
              'Intl 1924':     (6378.388,    6356.911946,   1 / 297.0),
              'Clarke (1880)': (6378.249145, 6356.51486955, 1 / 293.465),
              'GRS-67':        (6378.1600,   6356.774719,   1 / 298.25),
              }

def arc_degrees(arcminutes=0, arcseconds=0):
    """Calculate the decimal equivalent of the sum of ``arcminutes`` and
    ``arcseconds`` in degrees."""
    if arcminutes is None:
        arcminutes = 0
    if arcseconds is None:
        arcseconds = 0
    arcmin = float(arcminutes)
    arcsec = float(arcseconds)
    return arcmin * 1 / 60. + arcsec * 1 / 3600.

def kilometers(miles=0, feet=0, nautical=0):
    d = 0
    if feet:
        miles += feet / ft(1.0)
    if nautical:
        d += nautical / nm(1.0)
    d += miles * 1.609344
    return d

def miles(kilometers=0, feet=0, nautical=0):
    d = 0
    if nautical:
        kilometers += nautical / nm(1.0)
    if feet:
        d += feet / ft(1.0)
    d += kilometers * 0.621371192
    return d

def feet(miles=0, kilometers=0, nautical=0):
    d = 0
    if nautical:
        kilometers += nautical / nm(1.0)
    if kilometers:
        miles += mi(kilometers)
    d += miles * 5280
    return d

def nautical(kilometers=0, miles=0, feet=0):
    d = 0
    if feet:
        miles += feet / ft(1.0)
    if miles:
        kilometers += km(miles)
    d += kilometers / 1.852
    return d

km = kilometers
mi = miles
ft = feet
nm = nautical


class Distance(object):
    def __init__(self, kilometers=0, miles=0, feet=0, nautical=0):
        """Initialize a Distance whose length is the sum of all the units
        measured in the constructor (kilometers, miles, feet, nautical miles).
        """
        kilometers += km(miles=miles, feet=feet, nautical=nautical)
        self._kilometers = kilometers

    @property
    def kilometers(self):
        return self._kilometers
    
    @property
    def miles(self):
        return miles(self.kilometers)

    @property
    def feet(self):
        return feet(self.miles)

    @property
    def nautical(self):
        return nautical(self.kilometers)

    # Sadly, just aliasing the above properties with their abbreviations does
    # not work when they are subclassed. The easiest way I could find to
    # make this work without using a metaclass was to write more full-fledged
    # definitions...

    @property
    def mi(self):
        return self.miles
    
    @property
    def km(self):
        return self.kilometers
    
    @property
    def ft(self):
        return self.feet

    @property
    def nm(self):
        return self.nautical

    def __add__(self, other):
        """Return a new Distance of length ``self`` + ``other``."""
        if isinstance(other, Distance):
            return Distance(self.kilometers + other.kilometers)
        else:
            raise TypeError("Distance must be added with Distance.")

    def __sub__(self, other):
        """Return a new Distance of length ``self`` - ``other``."""
        if isinstance(other, Distance):
            return Distance(self.kilometers - other.kilometers)
        else:
            raise TypeError("Distance must be subtracted from Distance.")
        
    def __mul__(self, other):
        """Return a new Distance ``other`` times the length of ``self``,
        ``other`` is a number (int, float, long, or Decimal).
        """
        if isinstance(other, (int, float, long, Decimal)):
            other = float(other)
            return Distance(self.kilometers * other)
        else:
            raise TypeError("Distance must be multiplied by number.")

    def __div__(self, other):
        """If ``other`` is a number (int, float, long, or Decimal), return
        a new Distance of length ``self`` / ``other``.
        
        If ``other`` is a Distance, return the fraction given by
        ``self`` / ``other``.
        """
        if isinstance(other, Distance):
            return float(self.kilometers) / other.kilometers
        elif isinstance(other, (int, float, long, Decimal)):
            other = float(other)
            return Distance(self.kilometers / other)
        else:
            raise TypeError("Distance must be divided by Distance or number.")

    def __nonzero__(self):
        """Return whether or not this Distance is 0 units in length."""
        return bool(self.kilometers)


class GeodesicDistance(Distance):
    def __init__(self, a, b):
        """Initialize a Distance whose length is the distance between the two
        geodesic points ``a`` and ``b``, using the ``calculate`` method to
        determine this distance.
        """
        if isinstance(a, basestring):
            a = util.parse_geo(a)
        if isinstance(b, basestring):
            b = util.parse_geo(b)
        
        self.a = a
        self.b = b
        
        if a and b:
            self.calculate()

    def calculate(self):
        """Calculate and set the distance between ``self.a`` and ``self.b``,
        which should be two geodesic points. Since there are multiple formulas
        to calculate this, implementation is left up to the subclass.
        """
        raise NotImplementedError

    @property
    def kilometers(self):
        raise NotImplementedError

class GreatCircleDistance(GeodesicDistance):
    """Use spherical geometry to calculate the surface distance between two
    geodesic points. This formula can be written many different ways, including
    just the use of the spherical law of cosines or the haversine formula.
    
    The class member ``RADIUS`` indicates which radius of the earth to use,
    in kilometers. The default is to use the module constant ``EARTH_RADIUS``,
    which uses the average great-circle radius.
    """
    
    RADIUS = EARTH_RADIUS
    
    def calculate(self):
        lat1, lng1 = map(radians, self.a)
        lat2, lng2 = map(radians, self.b)
        
        sin_lat1, cos_lat1 = sin(lat1), cos(lat1)
        sin_lat2, cos_lat2 = sin(lat2), cos(lat2)
        
        delta_lng = lng2 - lng1
        cos_delta_lng, sin_delta_lng = cos(delta_lng), sin(delta_lng)
        
        central_angle = acos(sin_lat1 * sin_lat2 +
                             cos_lat1 * cos_lat2 * cos_delta_lng)
        
        # From http://en.wikipedia.org/wiki/Great_circle_distance:
        #   Historically, the use of this formula was simplified by the
        #   availability of tables for the haversine function. Although this
        #   formula is accurate for most distances, it too suffers from
        #   rounding errors for the special (and somewhat unusual) case of
        #   antipodal points (on opposite ends of the sphere). A more
        #   complicated formula that is accurate for all distances is: (below)
        
        d = atan2(sqrt((cos_lat2 * sin_delta_lng) ** 2 +
                       (cos_lat1 * sin_lat2 -
                        sin_lat1 * cos_lat2 * cos_delta_lng) ** 2),
                  sin_lat1 * sin_lat2 + cos_lat1 * cos_lat2 * cos_delta_lng)
        
        self.radians = d
    
    @property
    def kilometers(self):
        return self.RADIUS * self.radians
    

class VincentyDistance(GeodesicDistance):
    """Calculate the geodesic distance between two points using the formula
    devised by Thaddeus Vincenty, with an accurate ellipsoidal model of the
    earth.
    
    The class attribute ``ELLIPSOID`` indicates which ellipsoidal model of the
    earth to use. If it is a string, it is looked up in the ELLIPSOIDS
    dictionary to obtain the major and minor semiaxes and the flattening.
    Otherwise, it should be a tuple with those values. The most globally
    accurate model is WGS-84. See the comments above the ELLIPSOIDS dictionary
    for more information.
    """

    ELLIPSOID = ELLIPSOIDS['WGS-84']
    
    def calculate(self):
        lat1, lng1 = map(radians, self.a)
        lat2, lng2 = map(radians, self.b)
        
        if isinstance(self.ELLIPSOID, basestring):
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
        
        iter_limit = 20
        
        while abs(lambda_lng - lambda_prime) > 10e-12 and iter_limit > 0:
            sin_lambda_lng, cos_lambda_lng = sin(lambda_lng), cos(lambda_lng)
            
            sin_sigma = sqrt((cos_reduced2 * sin_lambda_lng) ** 2 +
                             (cos_reduced1 * sin_reduced2 - sin_reduced1 *
                              cos_reduced2 * cos_lambda_lng) ** 2)
            
            if sin_sigma == 0:
                # Coincident points
                self._kilometers = self.initial_bearing = self.final_bearing = 0
                return
            
            cos_sigma = (sin_reduced1 * sin_reduced2 +
                         cos_reduced1 * cos_reduced2 * cos_lambda_lng)
            
            sigma = atan2(sin_sigma, cos_sigma)
            
            sin_alpha = cos_reduced1 * cos_reduced2 * sin_lambda_lng / sin_sigma
            cos_sq_alpha = 1 - sin_alpha ** 2
            
            if cos_sq_alpha != 0:
                cos2_sigma_m = cos_sigma - 2 * (sin_reduced1 * sin_reduced2 /
                                                cos_sq_alpha)
            else:
                cos2_sigma_m = 0.0 # Equatorial line
            
            C = f / 16. * cos_sq_alpha * (4 + f * (4 - 3 * cos_sq_alpha))
            
            lambda_prime = lambda_lng
            lambda_lng = (delta_lng + (1 - C) * f * sin_alpha *
                          (sigma + C * sin_sigma *
                           (cos2_sigma_m + C * cos_sigma * 
                            (-1 + 2 * cos2_sigma_m ** 2))))
            iter_limit -= 1
            
        if iter_limit == 0:
            raise ValueError("Vincenty formula failed to converge!")
        
        u_sq = cos_sq_alpha * (major ** 2 - minor ** 2) / minor ** 2
        
        A = 1 + u_sq / 16384. * (4096 + u_sq * (-768 + u_sq *
                                                (320 - 175 * u_sq)))
        
        B = u_sq / 1024. * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))
        
        delta_sigma = (B * sin_sigma *
                       (cos2_sigma_m + B / 4. *
                        (cos_sigma * (-1 + 2 * cos2_sigma_m ** 2) -
                         B / 6. * cos2_sigma_m * (-3 + 4 * sin_sigma ** 2) *
                         (-3 + 4 * cos2_sigma_m ** 2))))
        
        s = minor * A * (sigma - delta_sigma)
        
        sin_lambda, cos_lambda = sin(lambda_lng), cos(lambda_lng)
        
        alpha_1 = atan2(cos_reduced2 * sin_lambda,
                        cos_reduced1 * sin_reduced2 -
                        sin_reduced1 * cos_reduced2 * cos_lambda)
        
        alpha_2 = atan2(cos_reduced1 * sin_lambda,
                        cos_reduced1 * sin_reduced2 * cos_lambda -
                        sin_reduced1 * cos_reduced2)
        
        self._kilometers = s
        self.initial_bearing = (360 + degrees(alpha_1)) % 360
        self.final_bearing = (360 + degrees(alpha_2)) % 360

    @property
    def kilometers(self):
        return self._kilometers

    @property
    def forward_azimuth(self):
        return self.initial_bearing


# Set the default distance formula to the most generally accurate.
distance = VincentyDistance


def destination(start, bearing, distance, radius=EARTH_RADIUS):
    lat1, lng1 = map(radians, start)
    bearing = radians(bearing)
    
    if isinstance(distance, Distance):
        distance = distance.kilometers
        
    d_div_r = float(distance) / radius
    
    lat2 = asin(sin(lat1) * cos(d_div_r) +
                cos(lat1) * sin(d_div_r) * cos(bearing))
    
    lng2 = lng1 + atan2(sin(bearing) * sin(d_div_r) * cos(lat1),
                        cos(d_div_r) - sin(lat1) * sin(lat2))
    
    return (degrees(lat2), degrees(lng2))


def vincenty_destination(start, bearing, distance,
                         ellipsoid=ELLIPSOIDS['WGS-84']):
    lat1, lng1 = map(radians, start)
    bearing = radians(bearing)
    
    if isinstance(distance, Distance):
        distance = distance.kilometers
    
    if isinstance(ellipsoid, basestring):
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
    
    A = 1 + u_sq / 16384. * (4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq)))
    B = u_sq / 1024. * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))

    sigma = distance / (minor * A)
    sigma_prime = 2 * pi
    
    while abs(sigma - sigma_prime) > 10e-12:
        cos2_sigma_m = cos(2 * sigma1 + sigma)
        sin_sigma, cos_sigma = sin(sigma), cos(sigma)
        delta_sigma = B * sin_sigma * (cos2_sigma_m + B / 4. *
                                       (cos_sigma * (-1 + 2 * cos2_sigma_m) -
                                        B / 6. * cos2_sigma_m *
                                        (-3 + 4 * sin_sigma ** 2) *
                                        (-3 + 4 * cos2_sigma_m ** 2)))
        sigma_prime = sigma
        sigma = distance / (minor * A) + delta_sigma
    
    sin_sigma, cos_sigma = sin(sigma), cos(sigma)
    
    lat2 = atan2(sin_reduced1 * cos_sigma +
                 cos_reduced1 * sin_sigma * cos_bearing,
                 (1 - f) * sqrt(sin_alpha ** 2 +
                                (sin_reduced1 * sin_sigma -
                                 cos_reduced1 * cos_sigma * cos_bearing) ** 2))
    
    lambda_lng = atan2(sin_sigma * sin_bearing,
                       cos_reduced1 * cos_sigma -
                       sin_reduced1 * sin_sigma * cos_bearing)
    
    C = f / 16. * cos_sq_alpha * (4 + f * (4 - 3 * cos_sq_alpha))
    
    delta_lng = (lambda_lng - (1 - C) * f * sin_alpha *
                 (sigma + C * sin_sigma *
                  (cos2_sigma_m + C * cos_sigma *
                   (-1 + 2 * cos2_sigma_m ** 2))))
    
    final_bearing = atan2(sin_alpha,
                          cos_reduced1 * cos_sigma * cos_bearing -
                          sin_reduced1 * sin_sigma)
    
    lng2 = lng1 + delta_lng
    
    return (degrees(lat2), degrees(lng2))
