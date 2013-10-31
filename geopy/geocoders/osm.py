"""
OpenStreetMaps geocoder, contributed by Alessandro Pasotti of ItOpen.
"""

from geopy.geocoders.base import Geocoder
from geopy.util import logger
from geopy.compat import urlencode


class Nominatim(Geocoder):
    """
    Nominatim geocoder for OpenStreetMap servers. Documentation at:
        http://wiki.openstreetmap.org/wiki/Nominatim
    """

    def __init__(self, format_string='%s', # pylint: disable=R0913
                        view_box=(-180,-90,180,90), country_bias=None, proxies=None):
        """
        :param string format_string:

        :param tuple view_box: Coordinates to restrict search within.

        :param string country_bias:
        """
        super(Nominatim, self).__init__(format_string, proxies)
        # XML needs all sorts of conditionals because of API differences
        # between geocode and reverse, so forget it
        self.country_bias = country_bias
        self.format_string = format_string
        self.view_box = view_box
        self.country_bias = country_bias

        self.api = "http://nominatim.openstreetmap.org/search"
        self.reverse_api = " http://nominatim.openstreetmap.org/reverse"

    def geocode(self, query, exactly_one=True):
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.
        """
        params = {
            'q': self.format_string % query,
            'view_box' : self.view_box,
            'format' : 'json',
        }

        if self.country_bias:
            params['countrycodes'] = self.country_bias

        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(self._call_geocoder(url), exactly_one)

    def reverse(self, query, exactly_one=True):
        """
        Returns a reverse geocoded location.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param bool exactly_one: Return one result or a list of results, if
            available.
        """
        lat, lon = [x.strip() for x in self._coerce_point_to_string(query).split(',')] # doh
        params = {
                'lat': lat,
                'lon' : lon,
                'format' : 'json',
          }
        url = "?".join((self.reverse_api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(self._call_geocoder(url), exactly_one)

    def _parse_json(self, places, exactly_one):
        if not isinstance (places, list):
            places = [places]
        if not len(places):
            return None

        def parse_code(place):
            latitude = place.get('lat', None)
            longitude = place.get('lon', None)
            placename = place.get('display_name', None)
            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)
            else:
                return None
            return (placename, (latitude, longitude))

        if exactly_one:
            return parse_code(places[0])
        else:
            return [parse_code(place) for place in places]
