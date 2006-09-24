import re
import math
import htmlentitydefs
from decimal import Decimal, getcontext

D = Decimal

# Unicode characters for symbols that appear in coordinate strings:
DEGREE = unichr(htmlentitydefs.name2codepoint['deg'])
ARCMIN = unichr(htmlentitydefs.name2codepoint['prime'])
ARCSEC = unichr(htmlentitydefs.name2codepoint['Prime'])

def parse_geo(string, regex=None):
    """Return a 2-tuple of Decimals parsed from ``string``. The default
    regular expression can parse most common coordinate formats,
    including:
        41.5;-81.0
        41.5,-81.0
        41.5 -81.0
        41.5 N -81.0 W
        -41.5 S;81.0 E
        23 26m 22s N 23 27m 30s E
        23 26' 22" N 23 27' 30" E
    ...and more whitespace and separator variations. UTF-8 characters such
    as the degree symbol, prime (arcminutes), and double prime (arcseconds)
    are also supported. Coordinates given from South and West will be
    converted appropriately (by switching their signs).
    
    A custom expression can be given using the ``regex`` argument. It can
    be a string or compiled regular expression, and must contain groups
    named 'latitude_degrees' and 'longitude_degrees'. It can optionally
    contain groups named 'latitude_minutes', 'latitude_seconds',
    'longitude_minutes', 'longitude_seconds' for increased precision.
    Optional single-character groups named 'north_south' and 'east_west' may
    be included to indicate direction, it is assumed that the coordinates
    reference North and East otherwise.
    """
    string = string.strip()
    if regex is None:
        sep = r"(\s*[;,\s]\s*)"
        try:
            lat, _, lng = re.split(sep, string)
            return (float(lat), float(lng))
        except ValueError:
            coord = r"(?P<%%s_degrees>-?\d+\.?\d*)%s?" % DEGREE
            arcmin = r"((?P<%%s_minutes>\d+\.?\d*)[m'%s])?" % ARCMIN
            arcsec = r'((?P<%%s_seconds>\d+\.?\d*)[s"%s])?' % ARCSEC
            coord_lat = r"\s*".join([coord % 'latitude',
                                     arcmin % 'latitude',
                                     arcsec % 'latitude'])
            coord_lng = r"\s*".join([coord % 'longitude',
                                     arcmin % 'longitude',
                                     arcsec % 'longitude'])
            direction_lat = r"(?P<north_south>[NS])?"
            direction_lng = r"(?P<east_west>[EW])?"
            lat = r"\s*".join([coord_lat, direction_lat])
            lng = r"\s*".join([coord_lng, direction_lng])
            regex = sep.join([lat, lng])

    match = re.match(regex, string)
    if match:
        d = match.groupdict()
        lat = d.get('latitude_degrees')
        lng = d.get('longitude_degrees')
        if lat:
            lat = float(lat)
            lat += arc_angle(d.get('latitude_minutes', 0),
                             d.get('latitude_seconds', 0))
            n_s = d.get('north_south', 'N').upper()
            if n_s == 'S':
                lat *= -1 
        if lng:
            lng = float(lng)
            lng += arc_angle(d.get('longitude_minutes', 0),
                             d.get('longitude_seconds', 0))
            e_w = d.get('east_west', 'E').upper()
            if e_w == 'W':
                lng *= -1
        return (lat, lng)
    else:
        return (None, None)


def arc_angle(arcminutes=None, arcseconds=None):
    """Calculate the decimal equivalent of the sum of ``arcminutes`` and
    ``arcseconds``."""
    if arcminutes is None:
        arcminutes = 0
    if arcseconds is None:
        arcseconds = 0
    arcmin = float(arcminutes)
    arcsec = float(arcseconds)
    return arcmin * 1 / 60. + arcsec * 1 / 3600.


# NOTE:
# The stuff below is for Decimal usage. It is not currently used by geopy,
# but it might be in the future.

# The following Decimal recipes were copied from the Decimal documentation:
# http://docs.python.org/lib/decimal-recipes.html

def pi():
    """Compute Pi to the current precision.

    >>> print pi()
    3.141592653589793238462643383
    
    """
    getcontext().prec += 2
    lasts, t, s, n, na, d, da = 0, D(3), 3, 1, 0, 0, 24
    while s != lasts:
        lasts = s
        n, na = n + na, na + 8
        d, da = d + da, da + 32
        t = (t * n) / d
        s += t
    getcontext().prec -= 2
    return +s

def exp(x):
    """Return e raised to the power of x.  Result type matches input type.

    >>> print exp(Decimal(1))
    2.718281828459045235360287471
    >>> print exp(Decimal(2))
    7.389056098930650227230427461
    >>> print exp(2.0)
    7.38905609893
    >>> print exp(2+0j)
    (7.38905609893+0j)
    
    """
    getcontext().prec += 2
    i, lasts, s, fact, num = 0, 0, 1, 1, 1
    while s != lasts:
        lasts = s    
        i += 1
        fact *= i
        num *= x     
        s += num / fact   
    getcontext().prec -= 2        
    return +s

def cos(x):
    """Return the cosine of x as measured in radians.

    >>> print cos(Decimal('0.5'))
    0.8775825618903727161162815826
    >>> print cos(0.5)
    0.87758256189
    >>> print cos(0.5+0j)
    (0.87758256189+0j)
    
    """
    getcontext().prec += 2
    i, lasts, s, fact, num, sign = 0, 0, 1, 1, 1, 1
    while s != lasts:
        lasts = s    
        i += 2
        fact *= i * (i - 1)
        num *= x * x
        sign *= -1
        s += num / fact * sign 
    getcontext().prec -= 2        
    return +s

def sin(x):
    """Return the sine of x as measured in radians.

    >>> print sin(Decimal('0.5'))
    0.4794255386042030002732879352
    >>> print sin(0.5)
    0.479425538604
    >>> print sin(0.5+0j)
    (0.479425538604+0j)
    
    """
    getcontext().prec += 2
    i, lasts, s, fact, num, sign = 1, 0, x, 1, x, 1
    while s != lasts:
        lasts = s    
        i += 2
        fact *= i * (i - 1)
        num *= x * x
        sign *= -1
        s += num / fact * sign
    getcontext().prec -= 2
    return +s

def asin(x):
    getcontext().prec += 2
    i, lasts, s, fact, num = D(0), 0, x, 1, x
    while s != lasts and i < 100:
        lasts = s
        i += 2
        fact *= (i - 1) / i
        num *= x * x
        s += fact * num / (i + 1)
    getcontext().prec -= 2
    return +s

def tan(x):
    return sin(x) / cos(x)

def atan(x):
    if x == D('-Inf'):
        return pi() / -2
    elif x == 0:
        return D(0)
    elif x == D('Inf'):
        return pi() / 2
    
    if x < -1:
        c = pi() / -2
        x = 1 / x
    elif x > 1:
        c = pi() / 2
        x = 1 / x
    else:
        c = 0
    
    getcontext().prec += 2
    x_squared = x ** 2
    y = x_squared / (1 + x_squared)
    y_over_x = y / x
    i, lasts, s, coeff, num = D(0), 0, y_over_x, 1, y_over_x
    while s != lasts:
        lasts = s    
        i += 2
        coeff *= i / (i + 1)
        num *= y
        s += num * coeff
    if c:
        s = c - s
    getcontext().prec -= 2
    return +s

