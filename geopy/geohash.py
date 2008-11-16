from geopy import Point

class Geohash(object):
    ENCODE_MAP = '0123456789bcdefghjkmnpqrstuvwxyz'
    DECODE_MAP = dict([(char, i) for i, char in enumerate(ENCODE_MAP)])

    def __init__(self, point_class=Point, precision=12):
        self.point_class = point_class
        self.precision = precision

    def encode(self, *args, **kwargs):
        precision = kwargs.pop('precision', self.precision)
        point = Point(*args, **kwargs)
        lat_min, latitude, lat_max = -90, 0, 90
        long_min, longitude, long_max = -180, 0, 180
        string = ''
        bytes = []
        odd_bit = False
        for i in xrange(precision):
            byte = 0
            for bit in (16, 8, 4, 2, 1):
                if odd_bit:
                    if point.latitude >= latitude:
                        byte |= bit
                        lat_min = latitude
                    else:
                        lat_max = latitude
                    latitude = (lat_min + lat_max) / 2.
                else:
                    if point.longitude >= longitude:
                        byte |= bit
                        long_min = longitude
                    else:
                        long_max = longitude
                    longitude = (long_min + long_max) / 2.
                odd_bit = not odd_bit
            bytes.append(byte) 
        return ''.join([self.ENCODE_MAP[byte] for byte in bytes])

    def decode(self, string):
        lat_min, latitude, lat_max = -90, 0, 90
        long_min, longitude, long_max = -180, 0, 180
        odd_bit = False
        for char in string:
            try:
                byte = self.DECODE_MAP[char]
            except KeyError:
                raise ValueError("Invalid hash: unexpected character %r." % (c,))
            else:
                for bit in (16, 8, 4, 2, 1):
                    if odd_bit:
                        if byte & bit:
                            lat_min = latitude
                        else:
                            lat_max = latitude
                        latitude = (lat_min + lat_max) / 2.
                    else:
                        if byte & bit:
                            long_min = longitude
                        else:
                            long_max = longitude
                        longitude = (long_min + long_max) / 2.
                    odd_bit = not odd_bit
        point = self.point_class((latitude, longitude))
        point.error = (lat_max - latitude, long_max - longitude)
        return point
