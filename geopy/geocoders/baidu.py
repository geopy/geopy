"""
:class:`.Baidu` is the Baidu Maps geocoder.
"""

from geopy.compat import urlencode
from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT
from geopy.exc import (
    GeocoderQueryError,
    GeocoderQuotaExceeded,
    GeocoderAuthenticationFailure,
)
from geopy.location import Location
from geopy.util import logger


__all__ = ("Baidu", )


class Baidu(Geocoder):
    """
    Geocoder using the Baidu Maps v2 API. Documentation at:
        http://developer.baidu.com/map/webservice-geocoding.htm
    """

    def __init__(
            self,
            api_key,
            scheme='http',
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
        ):
        """
        Initialize a customized Baidu geocoder using the v2 API.

        .. versionadded:: 1.0.0

        :param string api_key: The API key required by Baidu Map to perform
            geocoding requests. API keys are managed through the Baidu APIs
            console (http://lbsyun.baidu.com/apiconsole/key).

        :param string scheme: Use 'https' or 'http' as the API URL's scheme.
            Default is http and only http support.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.
        """
        super(Baidu, self).__init__(
            scheme=scheme, timeout=timeout, proxies=proxies
        )
        self.api_key = api_key
        self.scheme = scheme
        self.doc = {}
        self.api = 'http://api.map.baidu.com/geocoder/v2/'


    @staticmethod
    def _format_components_param(components):
        """
        Format the components dict to something Baidu understands.
        """
        return "|".join(
            (":".join(item)
             for item in components.items()
            )
        )

    def geocode(
            self,
            query,
            exactly_one=True,
            timeout=None
        ):
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        """
        params = {
            'ak': self.api_key,
            'output': 'json',
            'address': self.format_string % query,
        }

        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one=exactly_one
        )

    def reverse(self, query, timeout=None):  # pylint: disable=W0221
        """
        Given a point, find an address.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        """
        params = {
            'ak': self.api_key,
            'output': 'json',
            'location': self._coerce_point_to_string(query),
        }

        url = "?".join((self.api, urlencode(params)))

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_reverse_json(
            self._call_geocoder(url, timeout=timeout)
        )


    @staticmethod
    def _parse_reverse_json(page):
        """
        Parses a location from a single-result reverse API call.
        """
        place = page.get('result')

        location = place.get('formatted_address').encode('utf-8')
        latitude = place['location']['lat']
        longitude = place['location']['lng']

        return Location(location, (latitude, longitude), place)


    def _parse_json(self, page, exactly_one=True):
        """
        Returns location, (latitude, longitude) from JSON feed.
        """

        place = page.get('result', None)

        if not place:
            self._check_status(page.get('status'))
            return None

        def parse_place(place):
            """
            Get the location, lat, lng from a single JSON place.
            """
            location = place.get('level')
            latitude = place['location']['lat']
            longitude = place['location']['lng']
            return Location(location, (latitude, longitude), place)

        if exactly_one:
            return parse_place(place)
        else:
            return [parse_place(item) for item in place]

    @staticmethod
    def _check_status(status):
        """
        Validates error statuses.
        """
        if status == '0':
            # When there are no results, just return.
            return
        if status == '1':
            raise GeocoderQueryError(
                'Internal server error.'
            )
        elif status == '2':
            raise GeocoderQueryError(
                'Invalid request.'
            )
        elif status == '3':
            raise GeocoderAuthenticationFailure(
                'Authentication failure.'
            )
        elif status == '4':
            raise GeocoderQuotaExceeded(
                'Quota validate failure.'
            )
        elif status == '5':
            raise GeocoderQueryError(
                'AK Illegal or Not Exist.'
            )
        elif status == '101':
            raise GeocoderQueryError(
                'Your request was denied.'
            )
        elif status == '102':
            raise GeocoderQueryError(
                'IP/SN/SCODE/REFERER Illegal:'
            )
        elif status == '2xx':
            raise GeocoderQueryError(
                'Has No Privilleges.'
            )
        elif status == '3xx':
            raise GeocoderQuotaExceeded(
                'Quota Error.'
            )
        else:
            raise GeocoderQueryError('Unknown error')
