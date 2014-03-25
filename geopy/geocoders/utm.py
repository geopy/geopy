__author__ = 'brian'

from geopy.location import Location
from geopy.geocoders.base import Geocoder
from geopy.coordinate import Coordinate

class UTM(Geocoder):
    def __init__(self):
        super(UTM, self).__init__()

    def geocode(self, query, *args):
        """
        Geocoder that converts UTM string to digital lat/lon
        Only accepts zone letters with utm zone (not hemisphere N/S format)
        There is no way to differentiate between zone 'S' (valid) and 'S' for southern hemisphere,
        so we do not check for this.
        @param query: UTM string
        @param args: Not used
        @return: Location containing original UTM string and lat/lon
        @rtype: Location
        """
        utm = Coordinate.parse_utm(query)
        latlon = utm.as_gcs()
        output = Location(query, (latlon.lat, latlon.lon))
        return output
