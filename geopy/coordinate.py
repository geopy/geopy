__author__ = 'brian'

from math import pi, sqrt, pow, sin, degrees, tan, cos, radians
from string import split, upper


class Coordinate(object):
    def __init__(self):
        # Datum
        """
        Base Coordinate class. Not intended to be used directly. Holds useful constants and the parse_mgrs/parse_utm static method.

        """
        ellipsoid = 'WGS-84'
        self.datum = ellipsoid

        # Trivial constants
        self._deg2rad = pi / 180.0
        self._rad2deg = 180.0 / pi

        self._EquatorialRadius = 2
        self._eccentricitySquared = 3

        # Associate latitude and UTM sub-sectors
        self._NSminbound = {}
        self._NSzones = 'CDEFGHJKLMNPQRSTUVWX'
        for i in range(len(self._NSzones)):
            self._NSminbound[self._NSzones[i]] = -80 + (8 * i)

        #  id, Ellipsoid name, Equatorial Radius, square of eccentricity
        # Since we don't currently support non-WGS84 MGRS this is really only useful for UTM.
        # TODO: Add srs support for UTM.. low priority
        self._ellipsoid = {
            'Airy': (6377563, 0.00667054),
            'Australian National': (6378160, 0.006694542),
            'Bessel 1841': (6377397, 0.006674372),
            'Bessel 1841 (Nambia ': (6377484, 0.006674372),
            'Clarke 1866': (6378206, 0.006768658),
            'Clarke 1880': (6378249, 0.006803511),
            'Everest': (6377276, 0.006637847),
            'Fischer 1960 Mercury ': (6378166, 0.006693422),
            'Fischer 1968': (6378150, 0.006693422),
            'GRS 1967': (6378160, 0.006694605),
            'GRS 1980': (6378137, 0.00669438),
            'Helmert 1906': (6378200, 0.006693422),
            'Hough': (6378270, 0.00672267),
            'International': (6378388, 0.00672267),
            'Krassovsky': (6378245, 0.006693422),
            'Modified Airy': (6377340, 0.00667054),
            'Modified Everest': (6377304, 0.006637847),
            'Modified Fischer 1960': (6378155, 0.006693422),
            'South American 1969': (6378160, 0.006694542),
            'WGS 60': (6378165, 0.006693422),
            'WGS 66': (6378145, 0.006694542),
            'WGS-72': (6378135, 0.006694318),
            'WGS-84': (6378137, 0.00669438)
        }
        self.a, self.eccSquared = self._ellipsoid[self.datum]
        self.k0 = 0.9996
        self.eccPrimeSquared = (self.eccSquared) / (1 - self.eccSquared)

    @staticmethod
    def parse_mgrs(string):
        """
        Static method that parses an MGRS string and returns an MGRSCoordinate which can then be converted to UTM or LatLon using that instance's methods.
        The easting/northing must be balanced (equal number of digits) else it can't differentiate where one ends and other begins.
        @param string: The MGRS string to parse
        @rtype: MGRSCoordinate
        @raise Exception:
        """
        string = string.strip()
        # slice out zone, will be either 1 or 2 digits
        try:
            zone = int(string[0] + string[1])
            string = string[2:]
        except:
            zone = int(string[0])
            string = string[1:]

        # slice off letter
        utm_letter = string[0]
        string = string[1:]
        # slice off square
        square = string[:2]
        string = string[2:]
        # get digits
        coord_length = len(string)
        if coord_length > 10 or coord_length < 2:
            raise Exception('coordinates too short or too long, expected 2 to 10 digits, got %s' % coord_length)

        # easting/northing units (decameter, km, etc.. based on precision given (coord length)
        # figure out how far to push it up the numberline
        numberline_delta = 5 - (coord_length / 2)
        multiplier = pow(10, numberline_delta)

        def _isodd(num):
            return num & 0x1

        if _isodd(coord_length):
            raise Exception('Got odd number of coordinate digits, cannot differentiate easting/northing')
        else:
            midpoint = coord_length / 2
            try:
                easting = int(string[:midpoint]) * multiplier
                northing = int(string[midpoint:]) * multiplier
            except:
                raise Exception('Encountered problem parsing grid digits, probably found a non-numeric value')
        return MGRSCoordinate(zone, utm_letter, square, easting, northing)

    @staticmethod
    def parse_utm(string, delimiter=' '):
        """
        Static method that parses a UTM string and returns a UTMCoordinate which can then be converted to MGRS or LatLon using that instance's methods.
        Input must be of the form [0-9]{1,2}[A-Za-z] [0-9]+ [0-9]+
        That is, 1 or 2 digits for the zone, followed by UTM zone letter, space, then easting in meters, space, then northing in meters
        Note that it does not use a regexp to parse this, but rather uses the spaces as delimiters and the fact that the last token of the first part will always be alphabetic
        @param string: The UTM string to parse. Only supports the zone letter convention, not hemisphere e.g. 17T 630084 4833438
        @param delimiter: Optional delimiter to override default space
        @rtype UTMCoordinate
        @raise Exception:
        """
        string = string.strip()
        zone_str, easting, northing = split(string, delimiter)
        # slice out zone, will be either 1 or 2 digits, expecting something like 4N or 12S or 02S, etc..
        try:
            zone = int(zone_str[0] + zone_str[1])
            utm_letter = upper(zone_str[2:])  # hemisphere should be the last bit
        except:
            try:
                zone = int(zone_str[0])
                utm_letter = upper(zone_str[1:])  # hemisphere should be the last bit
            except:
                raise Exception("Couldn't parse out zone, expected [0-9]{1,2}[A-Za-z], got %s" % string[0:2])
        # int-ify easting/northing
        try:
            easting = int(easting)
            northing = int(northing)
        except:
            raise Exception('Encountered problem parsing grid digits, probably found a non-numeric value')

        return UTMCoordinate(zone=zone, utm_letter=utm_letter, easting=easting, northing=northing)

    def _get_utm_letter(self, lat):
        """ Returns the main letter designator for a latitude given in decimal Lat.
        """
        for i in self._NSminbound.keys():
            x = self._NSminbound[i]
            if x <= lat < x + 8:
                return i
        raise Exception('Outside of UTM area. Probably have an invalid latitude')


class GCSCoordinate(Coordinate):
    lat = None
    lon = None

    # TODO: Would be nice to have DMS parsing support someday?
    # Problem is there are so many disparate variations.
    # Still would like to look into this on a rainy day.
    def __init__(self, lat, lon):
        """
        Create GCSCoordinate from digital lat/lon.
        @param lat: Latitude in digital degrees, + for northern hemisphere, - for south
        @param lon: Longitude in digital degrees, + for eastern hemisphere, - for west
        """
        super(GCSCoordinate, self).__init__()
        self.lat = lat
        self.lon = lon

    def __repr__(self):
        """
        String representation of GCS as DD. Does not display DMS

        @return: String representation of GCS
        @rtype: str
        """
        return str("Lat " + str(self.lat) + ", Lon " + str(self.lon))

    def as_utm(self):
        """ Conversion from decimal lat and long into a UTM list.

              converts lat/long to UTM coords.  Equations from USGS Bulletin 1532
              East Longitudes are positive, West longitudes are negative.
              North latitudes are positive, South latitudes are negative
              Lat and Long are in decimal degrees
        @rtype : UTMCoordinate
        """
        lat = self.lat

        #Make sure the longitude is between -180.00 .. 179.9
        lon = (self.lon + 180) - int((self.lon + 180) / 360) * 360 - 180  # -180.00 .. 179.9

        # Radians
        lat_radians = radians(lat)
        lon_radians = radians(lon)

        zone_number = int((lon + 180) / 6) + 1

        if 56.0 <= lat < 64.0 and 3.0 <= lon < 12.0:
            zone_number = 32

        # Special zones for Svalbard
        if 72.0 <= lat < 84.0:
            if 0.0 <= lon < 9.0:
                zone_number = 31
            elif 9.0 <= lon < 21.0:
                zone_number = 33
            elif 21.0 <= lon < 33.0:
                zone_number = 35
            elif 33.0 <= lon < 42.0:
                zone_number = 37

        lon_origin = (zone_number - 1) * 6 - 180 + 3  #+3 puts origin in middle of zone
        lon_origin_radians = radians(lon_origin)

        N = self.a / sqrt(1 - self.eccSquared * sin(lat_radians) * sin(lat_radians))
        T = tan(lat_radians) * tan(lat_radians)
        C = self.eccPrimeSquared * cos(lat_radians) * cos(lat_radians)
        A = cos(lat_radians) * (lon_radians - lon_origin_radians)

        # Huh... I'm not going to touch that...
        M = self.a * ((1 - self.eccSquared / 4
                       - 3 * self.eccSquared * self.eccSquared / 64
                       - 5 * self.eccSquared * self.eccSquared * self.eccSquared / 256) * lat_radians
                      - (3 * self.eccSquared / 8
                         + 3 * self.eccSquared * self.eccSquared / 32
                         + 45 * self.eccSquared * self.eccSquared * self.eccSquared / 1024) * sin(2 * lat_radians)
                      + (
                          15 * self.eccSquared * self.eccSquared / 256 + 45 * self.eccSquared * self.eccSquared * self.eccSquared / 1024) * sin(
            4 * lat_radians)
                      - (35 * self.eccSquared * self.eccSquared * self.eccSquared / 3072) * sin(6 * lat_radians))

        utm_easting = (self.k0 * N * (
            A + (1 - T + C) * (A ** 3) / 6 + (5 - 18 * T + T * T + 72 * C - 58 * self.eccPrimeSquared) * (
                A ** 5) / 120) + 500000.0)

        utm_northing = (self.k0 * (M + N * tan(lat_radians) *
                                   (A * A / 2 + (5 - T + 9 * C + 4 * C * C) * (A ** 4)
                                    / 24 + (61 - 58 * T + T * T + 600 * C - 330 * self.eccPrimeSquared) * (
                                       A ** 6) / 720)))

        if lat < 0:
            utm_northing += 10000000.0  # 10000000 meter offset for southern hemisphere

        # Returns as list
        letter = self._get_utm_letter(lat)
        return UTMCoordinate(zone=zone_number, utm_letter=letter, easting=round(utm_easting),
                             northing=round(utm_northing))


class UTMCoordinate(Coordinate):
    zone = None
    utm_letter = None
    easting = None
    northing = None

    def __init__(self, zone, utm_letter, easting, northing):
        """
        Create a UTMCoordinate instance
        @param zone: UTM Zone, numeric string
        @param utm_letter: Letter for UTM zone
        @param easting: Easting in meters
        @param northing: Northing in meters
        @rtype: UTMCoordinate
        """
        super(UTMCoordinate, self).__init__()
        self.zone = zone
        self.utm_letter = utm_letter
        self.easting = easting
        self.northing = northing

    def __repr__(self):
        return str(self.zone) + str(self.utm_letter) + " " + str(self.easting) + "E " + str(self.northing) + "N"

    def as_gcs(self):
        """ Conversion from utm to LL

              converts UTM coords to lat/long.  Equations from USGS Bulletin 1532
              East Longitudes are positive, West longitudes are negative.
              North latitudes are positive, South latitudes are negative
              Lat and Long are in decimal degrees.
              @rtype GCSCoordinate
        """

        northing = self.northing
        easting = self.easting
        subzone = self.utm_letter
        zone = self.zone
        e1 = (1 - sqrt(1 - self.eccSquared)) / (1 + sqrt(1 - self.eccSquared))

        x = easting - 500000.0  # remove 500,000 meter offset for longitude
        y = northing

        zone_letter = subzone
        zone_number = int(zone)
        if zone_letter >= 'N':
            pass
        else:  # southern hemisphere
            y -= 10000000.0         # remove 10,000,000 meter offset used for southern hemisphere

        lon_origin = (zone_number - 1) * 6 - 180 + 3  # +3 puts origin in middle of zone

        M = y / self.k0
        mu = M / (self.a * (
            1 - self.eccSquared / 4 - 3 * self.eccSquared * self.eccSquared / 64 - 5 * (self.eccSquared ** 3) / 256))

        phi1Rad = (mu + (3 * e1 / 2 - 27 * e1 * e1 * e1 / 32) * sin(2 * mu)
                   + (21 * e1 * e1 / 16 - 55 * e1 * e1 * e1 * e1 / 32) * sin(4 * mu)
                   + (151 * e1 * e1 * e1 / 96) * sin(6 * mu))

        N1 = self.a / sqrt(1 - self.eccSquared * sin(phi1Rad) * sin(phi1Rad))
        T1 = tan(phi1Rad) * tan(phi1Rad)
        C1 = self.eccPrimeSquared * cos(phi1Rad) * cos(phi1Rad)
        R1 = self.a * (1 - self.eccSquared) / pow(1 - self.eccSquared * sin(phi1Rad) * sin(phi1Rad), 1.5)
        D = x / (N1 * self.k0)

        lat = phi1Rad - (N1 * tan(phi1Rad) / R1) * (
            D * D / 2 - (5 + 3 * T1 + 10 * C1 - 4 * C1 * C1 - 9 * self.eccPrimeSquared) * D * D * D * D / 24
            + (
                  61 + 90 * T1 + 298 * C1 + 45 * T1 * T1 - 252 * self.eccPrimeSquared - 3 * C1 * C1) * D * D * D * D * D * D / 720)
        lat = degrees(lat)

        lon = (D - (1 + 2 * T1 + C1) * D * D * D / 6 + (
                                                           5 - 2 * C1 + 28 * T1 - 3 * C1 * C1 + 8 * self.eccPrimeSquared + 24 * T1 * T1) * D * D * D * D * D / 120) / cos(
            phi1Rad)
        lon = lon_origin + degrees(lon)

        # Remove extraneous precision
        lon = round(lon, 5)
        lat = round(lat, 5)

        return GCSCoordinate(lat=lat, lon=lon)


class MGRSCoordinate(Coordinate):
    zone = None
    utm_letter = None
    square = None
    easting = None
    northing = None

    def __init__(self, zone, utm_letter, square, easting, northing):
        """

        @param zone: UTM Zone
        @param utm_letter: UTM Letter
        @param square: 100k Square
        @param easting: Easting in meters
        @param northing: Northing in meters
        """
        super(MGRSCoordinate, self).__init__()
        self.zone = zone
        self.utm_letter = utm_letter
        self.square = square
        self.easting = easting
        self.northing = northing

    def __repr__(self):
        """
        Output the MGRS coordinate in the typical format.
        @return: string representation of coordinate
        @rtype: str
        """
        return str(self.zone) + str(self.utm_letter) + str(self.square) + str(self.easting) + str(self.northing)

    def as_gcs(self):
        """
        Convert MGRS directly to GCSCoordinate. Converts it to UTM internally, then UTM to Lat/Lon.
        @return: A GCSCoordinate (Lat/Lon)
        @rtype: GCSCoordinate
        """
        utm = self.as_utm()
        return utm.as_gcs()

    def as_utm(self):
        """
        Convert MGRS to UTM. Used by as_gcs()
        @return: a UTMCoordinate
        @rtype : UTMCoordinate
        """
        # Zone keys
        EW = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
        NS = 'ABCDEFGHJKLMNPQRSTUV'

        # Easting
        S = int(self.zone) - 1
        S %= 3
        S *= 8
        S %= 24  # Index of first box in this zone
        myindex = EW.find(self.square[0]) - S
        eastoffset = 100000. + (100000. * myindex) + int(self.easting)

        # Northing
        # Get the northing
        S = int(self.zone)
        S %= 2
        if S:
            # Odd number zone start @ A
            ns = NS
        else:
            # Even @ F
            ns = NS[5:] + NS[:5]
        # Northing bounds
        NBd = self._AllowedNorthingFromZone(self.utm_letter)


        # Offset from N (use EW for major zone seprators since there are letter beyond V in this scale)
        if EW.find(self.utm_letter) >= EW.find('N'):
            # Norther hemisphere, second letter of 100ksquare
            offset = ns.find(self.square[1])
            northing = offset * 100000. + float(self.northing)
            while northing < NBd[0] * 0.95:
                # One spin around the alphabet
                northing += 2000000.
        else:
            northing = 10000000.
            # Determine how many boxes to move down from last box before equator
            offset = len(ns) - ns.find(self.square[1])
            # minus 100km box + northing residual
            offset = (-100000 * offset) + float(self.northing)
            northing += offset
            # the 1.05 factor is there to compensate for loos of precision.
            while northing > NBd[1] * 1.05:
                # One Spin around the alphabet
                northing -= 2000000.
        utm = UTMCoordinate(self.zone, self.utm_letter, easting=eastoffset, northing=northing)
        return utm

    def _northing_helper(self, Lat):
        """
        I don't really know what this does. Does anyone? Seems to be correct..
        @param Lat:
        @return: max northing (meters) for a given latitude.
        @rtype: int
        """
        Long = 0

        #Make sure the longitude is between -180.00 .. 179.9
        LongTemp = (Long + 180) - int((Long + 180) / 360) * 360 - 180 # -180.00 .. 179.9

        # Radians
        LatRad = radians(Lat)
        LongRad = radians(LongTemp)

        zone = int((LongTemp + 180) / 6) + 1

        if Lat >= 56.0 and Lat < 64.0 and LongTemp >= 3.0 and LongTemp < 12.0:
            zone = 32

        # Special zones for Svalbard
        if 72.0 <= Lat < 84.0:
            if 0.0 <= LongTemp < 9.0:
                zone = 31
            elif 9.0 <= LongTemp < 21.0:
                zone = 33
            elif 21.0 <= LongTemp < 33.0:
                zone = 35
            elif 33.0 <= LongTemp < 42.0:
                zone = 37

        lon_origin = (zone - 1) * 6 - 180 + 3  # +3 puts origin in middle of zone
        long_origin_radian = radians(lon_origin)

        N = self.a / sqrt(1 - self.eccSquared * sin(LatRad) * sin(LatRad))
        T = tan(LatRad) * tan(LatRad)
        C = self.eccPrimeSquared * cos(LatRad) * cos(LatRad)
        A = cos(LatRad) * (LongRad - long_origin_radian)

        # Huh... I'm not going to touch that...
        M = self.a * ((1 - self.eccSquared / 4
                       - 3 * self.eccSquared * self.eccSquared / 64
                       - 5 * self.eccSquared * self.eccSquared * self.eccSquared / 256) * LatRad
                      - (3 * self.eccSquared / 8
                         + 3 * self.eccSquared * self.eccSquared / 32
                         + 45 * self.eccSquared * self.eccSquared * self.eccSquared / 1024) * sin(2 * LatRad)
                      + (
                          15 * self.eccSquared * self.eccSquared / 256 + 45 * self.eccSquared * self.eccSquared * self.eccSquared / 1024) * sin(
            4 * LatRad)
                      - (35 * self.eccSquared * self.eccSquared * self.eccSquared / 3072) * sin(6 * LatRad))

        UTMNorthing = (self.k0 * (M + N * tan(LatRad) * (A * A / 2 + (5 - T + 9 * C + 4 * C * C) * (A ** 4) / 24
                                                         + (61
                                                            - 58 * T
                                                            + T * T
                                                            + 600 * C
                                                            - 330 * self.eccPrimeSquared) * (A ** 6) / 720)))

        if Lat < 0:
            UTMNorthing += 10000000.0  # 10000000 meter offset for southern hemisphere

        return round(UTMNorthing)

    def _AllowedNorthingFromZone(self, zone):
        """  Returns a list of min and max UTM Northing for a given Zone.
             This is a utility function for MGRStoUTM.
        @param zone: UTM zone
        @return: Min/Max UTM Northing for a given UTM zone
        @rtype: tuple
        """
        mn = self._NSminbound[zone]
        mx = mn + 8
        Nmin = self._northing_helper(mn)
        if zone == 'M':
            Nmax = 10000000
        else:
            Nmax = self._northing_helper(mx)

        return [Nmin, Nmax]
