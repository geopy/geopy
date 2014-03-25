from geopy.location import Location
from geopy.geocoders.base import Geocoder
from geopy.coordinate import Coordinate


class MGRS(Geocoder):
    def __init__(self):
        super(MGRS, self).__init__()

    def geocode(self, query, *args):
        """
        Geocoder that will take MGRS and return digital lat/lon
        Expects format such as 4QFJ12345678
        Zone digits (1 or 2 prefix) and 3 alphanumerics for UTM zone and 100k square are mandatory
        Trailing digits for easting/northing must be 2-10 digits long (1-5 each)
        Note: Does not work on older pre-WGS84 schema. Only supports MGRS-New (AA-scheme).
        If you don't understand what this means and you are using current WGS84 data you're probably fine
        If you are using old coords (e.g. Vietnam-era MGRS data) you must convert it to the AA-scheme.
        There are collisions between MGRS-Old and MGRS-New (some strings are valid in both) so be careful.
        @param query: MGRS String
        @param args: Not used
        @return: Location containing original MGRS string and lat/lon
        @rtype: Location
        """
        mgrs = Coordinate.parse_mgrs(query)
        latlon = mgrs.as_gcs()
        output = Location(query, (latlon.lat, latlon.lon))
        return output
