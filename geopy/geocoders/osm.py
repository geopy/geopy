"""
OpenStreetMaps geocoder, contributed by Alessandro Pasotti of ItOpen.
"""

from geopy.geocoders.base import Geocoder, DEFAULT_FORMAT_STRING, \
    DEFAULT_TIMEOUT
from geopy.compat import urlencode
from geopy.location import Location
from geopy.util import logger


class Nominatim(Geocoder):
    """
    Nominatim geocoder for OpenStreetMap servers. Documentation at:
        https://wiki.openstreetmap.org/wiki/Nominatim

    Note that Nominatim does not support SSL.
    """

    def __init__(self, format_string=DEFAULT_FORMAT_STRING, # pylint: disable=R0913
                        view_box=(-180, -90, 180, 90), country_bias=None,
                        timeout=DEFAULT_TIMEOUT, proxies=None):
        """
        :param string format_string: String containing '%s' where the
            string to geocode should be interpolated before querying the
            geocoder. For example: '%s, Mountain View, CA'. The default
            is just '%s'.

        :param tuple view_box: Coordinates to restrict search within.

        :param string country_bias: Bias results to this country.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

            .. versionadded:: 0.96
        """
        super(Nominatim, self).__init__(format_string, 'http', timeout, proxies)
        # XML needs all sorts of conditionals because of API differences
        # between geocode and reverse, so only implementing JSON format
        self.country_bias = country_bias
        self.format_string = format_string
        self.view_box = view_box
        self.country_bias = country_bias

        self.api = "%s://nominatim.openstreetmap.org/search" % self.scheme
        self.reverse_api = "%s://nominatim.openstreetmap.org/reverse" % self.scheme

    def geocode(self, query, exactly_one=True, timeout=None):
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call only,
            the value set during the geocoder's initialization.

            .. versionadded:: 0.97
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
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    def reverse(self, query, exactly_one=True, timeout=None):
        """
        Returns a reverse geocoded location.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call only,
            the value set during the geocoder's initialization.

            .. versionadded:: 0.97
        """
        lat, lon = [
            x.strip() for x in
            self._coerce_point_to_string(query).split(',')
        ] # doh
        params = {
            'lat': lat,
            'lon' : lon,
            'format' : 'json',
        }
        url = "?".join((self.reverse_api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    @staticmethod
    def parse_code(place):
        """
        Parse each resource.
        """
        latitude = place.get('lat', None)
        longitude = place.get('lon', None)
        placename = place.get('display_name', None)
        if latitude and longitude:
            latitude = float(latitude)
            longitude = float(longitude)
        return Location(placename, (latitude, longitude), place)

    def _parse_json(self, places, exactly_one):
        if places is None:
            return None
        if not isinstance(places, list):
            places = [places]
        if not len(places):
            return None
        if exactly_one is True:
            return self.parse_code(places[0])
        else:
            return [self.parse_code(place) for place in places]
