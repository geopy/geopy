import re
import htmlentitydefs
from distance import arc_degrees

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
            lat += arc_degrees(d.get('latitude_minutes', 0),
                               d.get('latitude_seconds', 0))
            n_s = d.get('north_south', 'N').upper()
            if n_s == 'S':
                lat *= -1 
        if lng:
            lng = float(lng)
            lng += arc_degrees(d.get('longitude_minutes', 0),
                               d.get('longitude_seconds', 0))
            e_w = d.get('east_west', 'E').upper()
            if e_w == 'W':
                lng *= -1
        return (lat, lng)
    else:
        return (None, None)

