"""
:class:`.GeocodeFarm` geocoder.
"""

from geopy.geocoders.base import Geocoder, DEFAULT_FORMAT_STRING, \
    DEFAULT_TIMEOUT
from geopy.location import Location
from geopy.util import logger
from geopy.exc import GeocoderAuthenticationFailure, GeocoderQuotaExceeded, \
    GeocoderServiceError
from geopy.compat import urlencode


__all__ = ("GeocodeFarm", )


class GeocodeFarm(Geocoder):
    """
    Geocoder using the GeocodeFarm API. Documentation at:
        https://www.geocode.farm/geocoding/free-api-documentation/
    """

    def __init__(
            self,
            api_key=None,
            format_string=DEFAULT_FORMAT_STRING,
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
            user_agent=None,
        ):  # pylint: disable=R0913
        """
        Create a geocoder for GeocodeFarm.

            .. versionadded:: 0.99

        :param str api_key: The API key required by GeocodeFarm to perform
            geocoding requests.

        :param str format_string: String containing '%s' where the
            string to geocode should be interpolated before querying the
            geocoder. For example: '%s, Mountain View, CA'. The default
            is just '%s'.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

        :param str user_agent: Use a custom User-Agent header.

            .. versionadded:: 1.12.0
        """
        super(GeocodeFarm, self).__init__(
            format_string, 'https', timeout, proxies, user_agent=user_agent
        )
        self.api_key = api_key
        self.format_string = format_string
        self.api = (
            "%s://www.geocode.farm/v3/json/forward/" % self.scheme
        )
        self.reverse_api = (
            "%s://www.geocode.farm/v3/json/reverse/" % self.scheme
        )

    def geocode(self, query, exactly_one=True, timeout=None):
        """
        Geocode a location query.

        :param str query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.
        """
        params = {
            'addr': self.format_string % query,
        }
        if self.api_key:
            params['key'] = self.api_key
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
            available. GeocodeFarm's API will always return at most one
            result.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.
        """
        try:
            lat, lon = [
                x.strip() for x in
                self._coerce_point_to_string(query).split(',')
            ]
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")
        params = {
            'lat': lat,
            'lon': lon
        }
        if self.api_key:
            params['key'] = self.api_key
        url = "?".join((self.reverse_api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    @staticmethod
    def parse_code(results):
        """
        Parse each resource.
        """
        places = []
        for result in results.get('RESULTS'):
            coordinates = result.get('COORDINATES', {})
            address = result.get('ADDRESS', {})
            latitude = coordinates.get('latitude', None)
            longitude = coordinates.get('longitude', None)
            placename = address.get('address_returned', None)
            if placename is None:
                placename = address.get('address', None)
            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)
            places.append(Location(placename, (latitude, longitude), result))
        return places

    def _parse_json(self, api_result, exactly_one):
        if api_result is None:
            return None
        geocoding_results = api_result["geocoding_results"]
        self._check_for_api_errors(geocoding_results)

        places = self.parse_code(geocoding_results)
        if exactly_one:
            return places[0]
        else:
            return places

    @staticmethod
    def _check_for_api_errors(geocoding_results):
        """
        Raise any exceptions if there were problems reported
        in the api response.
        """
        status_result = geocoding_results.get("STATUS", {})
        api_call_success = status_result.get("status", "") == "SUCCESS"
        if not api_call_success:
            access_error = status_result.get("access")
            access_error_to_exception = {
                'API_KEY_INVALID': GeocoderAuthenticationFailure,
                'OVER_QUERY_LIMIT': GeocoderQuotaExceeded,
            }
            exception_cls = access_error_to_exception.get(
                access_error, GeocoderServiceError
            )
            raise exception_cls(access_error)
