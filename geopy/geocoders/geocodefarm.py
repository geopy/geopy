"""
GeocodeFarm.com geocoder, contributed by Eric Palakovich Carr.
Register for a free account here: https://www.geocodefarm.com/dashboard/register/
Afterwards, check documentation here: https://www.geocodefarm.com/dashboard/documentation/
"""

from geopy.geocoders.base import Geocoder, DEFAULT_FORMAT_STRING, \
    DEFAULT_TIMEOUT
from geopy.location import Location
from geopy.util import logger
from geopy.exc import GeocoderAuthenticationFailure, GeocoderQuotaExceeded, \
    GeocoderServiceError
import urllib


# TODO: Determine what to put for `.. versionadded:: X.XX` strings throughout code
class GeocodeFarm(Geocoder):
    """
    GeocodeFarm geocoder. Documentation at (requires login, but free accounts are available):
        https://www.geocodefarm.com/dashboard/documentation/
    """

    def __init__(self, api_key=None, format_string=DEFAULT_FORMAT_STRING, # pylint: disable=R0913
                        timeout=DEFAULT_TIMEOUT, proxies=None):
        """
        :param string api_key: The API key required by GeocodeFarm to perform
            geocoding requests. API keys are managed the user Dashboard
            (https://www.geocodefarm.com/dashboard/).

        :param string format_string: String containing '%s' where the
            string to geocode should be interpolated before querying the
            geocoder. For example: '%s, Mountain View, CA'. The default
            is just '%s'.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.
        """
        super(GeocodeFarm, self).__init__(format_string, 'http', timeout, proxies)
        self.api_key = api_key
        self.format_string = format_string
        self.api = "%s://www.geocodefarm.com/api/forward/json/%s/" % (self.scheme, self.api_key)
        self.reverse_api = "%s://www.geocodefarm.com/api/reverse/json/%s/" % (self.scheme, self.api_key)

    def geocode(self, query, exactly_one=True, timeout=None):
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: This flag has no effect in this geocoder,
            since GeocodeFarm's API will always return only one result.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call only,
            the value set during the geocoder's initialization.
        """
        url = self.api + urllib.quote((self.format_string % query).encode('utf8'))
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

        :param bool exactly_one: This flag has no effect in this geocoder,
            since GeocodeFarm's API will always return only one result.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call only,
            the value set during the geocoder's initialization.
        """
        lat, lon = self._coerce_point_to_string(query).split(',')
        url = self.reverse_api + urllib.quote(("%s/%s" % (lat, lon)).encode('utf8'))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    @staticmethod
    def parse_code(place):
        """
        Parse each resource.
        """
        coordinates = place.get('COORDINATES', {})
        address = place.get('ADDRESS', {})
        latitude = coordinates.get('latitude', None)
        longitude = coordinates.get('longitude', None)
        placename = address.get('address_returned', None)
        if placename is None:
            placename = address.get('address', None)
        if latitude and longitude:
            latitude = float(latitude)
            longitude = float(longitude)
        return Location(placename, (latitude, longitude), place)

    def _parse_json(self, api_result, exactly_one):
        if api_result is None:
            return None
        geocoding_results = api_result["geocoding_results"]
        self._check_for_api_errors(geocoding_results)

        place = self.parse_code(geocoding_results)
        if exactly_one is True:
            return place
        else:
            return [place]  # GeocodeFarm always only returns one result

    @staticmethod
    def _check_for_api_errors(geocoding_results):
        # Raise any exceptions if there were problems reported
        # in the api response
        status_result = geocoding_results.get("STATUS", {})
        api_call_success = status_result.get("status", "") == "SUCCESS"
        if not api_call_success:
            access_error = status_result.get("access")
            access_error_to_exception = {
                'API_KEY_INVALID': GeocoderAuthenticationFailure,
                'OVER_QUERY_LIMIT': GeocoderQuotaExceeded,
            }
            exception_cls = access_error_to_exception.get(
                access_error, GeocoderServiceError)
            raise exception_cls(access_error)
