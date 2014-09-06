"""
Formatting...
"""

from geopy import units
from geopy.compat import py3k

if py3k:
    unichr = chr # pylint: disable=W0622

# Unicode characters for symbols that appear in coordinate strings.
DEGREE = unichr(176)
PRIME = unichr(8242)
DOUBLE_PRIME = unichr(8243)
ASCII_DEGREE = ''
ASCII_PRIME = "'"
ASCII_DOUBLE_PRIME = '"'
LATIN1_DEGREE = chr(176)
HTML_DEGREE = '&deg;'
HTML_PRIME = '&prime;'
HTML_DOUBLE_PRIME = '&Prime;'
XML_DECIMAL_DEGREE = '&#176;'
XML_DECIMAL_PRIME = '&#8242;'
XML_DECIMAL_DOUBLE_PRIME = '&#8243;'
XML_HEX_DEGREE = '&xB0;'
XML_HEX_PRIME = '&x2032;'
XML_HEX_DOUBLE_PRIME = '&x2033;'
ABBR_DEGREE = 'deg'
ABBR_ARCMIN = 'arcmin'
ABBR_ARCSEC = 'arcsec'

DEGREES_FORMAT = (
    "%(degrees)d%(deg)s %(minutes)d%(arcmin)s %(seconds)g%(arcsec)s"
)

UNICODE_SYMBOLS = {
    'deg': DEGREE,
    'arcmin': PRIME,
    'arcsec': DOUBLE_PRIME
}
ASCII_SYMBOLS = {
    'deg': ASCII_DEGREE,
    'arcmin': ASCII_PRIME,
    'arcsec': ASCII_DOUBLE_PRIME
}
LATIN1_SYMBOLS = {
    'deg': LATIN1_DEGREE,
    'arcmin': ASCII_PRIME,
    'arcsec': ASCII_DOUBLE_PRIME
}
HTML_SYMBOLS = {
    'deg': HTML_DEGREE,
    'arcmin': HTML_PRIME,
    'arcsec': HTML_DOUBLE_PRIME
}
XML_SYMBOLS = {
    'deg': XML_DECIMAL_DEGREE,
    'arcmin': XML_DECIMAL_PRIME,
    'arcsec': XML_DECIMAL_DOUBLE_PRIME
}
ABBR_SYMBOLS = {
    'deg': ABBR_DEGREE,
    'arcmin': ABBR_ARCMIN,
    'arcsec': ABBR_ARCSEC
}

def format_degrees(degrees, fmt=DEGREES_FORMAT, symbols=None):
    """
    TODO docs.
    """
    symbols = symbols or ASCII_SYMBOLS
    arcminutes = units.arcminutes(degrees=degrees - int(degrees))
    arcseconds = units.arcseconds(arcminutes=arcminutes - int(arcminutes))
    format_dict = dict(
        symbols,
        degrees=degrees,
        minutes=abs(arcminutes),
        seconds=abs(arcseconds)
    )
    return fmt % format_dict

DISTANCE_FORMAT = "%(magnitude)s%(unit)s"
DISTANCE_UNITS = {
    'km': lambda d: d,
    'm': lambda d: units.meters(kilometers=d),
    'mi': lambda d: units.miles(kilometers=d),
    'ft': lambda d: units.feet(kilometers=d),
    'nm': lambda d: units.nautical(kilometers=d),
    'nmi': lambda d: units.nautical(kilometers=d)
}

def format_distance(kilometers, fmt=DISTANCE_FORMAT, unit='km'):
    """
    TODO docs.
    """
    magnitude = DISTANCE_UNITS[unit](kilometers)
    return fmt % {'magnitude': magnitude, 'unit': unit}

_DIRECTIONS = [
    ('north', 'N'),
    ('north by east', 'NbE'),
    ('north-northeast', 'NNE'),
    ('northeast by north', 'NEbN'),
    ('northeast', 'NE'),
    ('northeast by east', 'NEbE'),
    ('east-northeast', 'ENE'),
    ('east by north', 'EbN'),
    ('east', 'E'),
    ('east by south', 'EbS'),
    ('east-southeast', 'ESE'),
    ('southeast by east', 'SEbE'),
    ('southeast', 'SE'),
    ('southeast by south', 'SEbS'),
]

DIRECTIONS, DIRECTIONS_ABBR = zip(*_DIRECTIONS)
ANGLE_DIRECTIONS = {
    n * 11.25: d
    for n, d
    in enumerate(DIRECTIONS)
}
ANGLE_DIRECTIONS_ABBR = {
    n * 11.25: d
    for n, d
    in enumerate(DIRECTIONS_ABBR)
}
