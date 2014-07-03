"""
:class:`.Baidu` is the Baidu Maps geocoder.
"""

import base64
import hashlib
import hmac
from geopy.compat import urlencode
from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT, DEFAULT_SCHEME
from geopy.exc import (
    GeocoderQueryError,
    GeocoderQuotaExceeded,
    ConfigurationError
)
from geopy.location import Location
from geopy.util import logger


class Baidu(Geocoder):
    """
    Geocoder using the Baidu Maps v2 API. Documentation at:
        http://developer.baidu.com/map/webservice-geocoding.htm
    """

    def __init__(self, ak=None, scheme='http', timeout=DEFAULT_TIMEOUT,
                  proxies=None):
        """
        Initialize a customized Baidu geocoder.

        API authentication is only required for Baidu Maps Premier customers.

        :param string ak: The API key required by Baidu Map to perform
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
        if not ak:
            raise ConfigurationError('Must provide ak.')
        self.ak = ak
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

    def geocode(self, query, bounds=None, region=None, # pylint: disable=W0221,R0913
                components=None,
                language=None, sensor=False, exactly_one=True, timeout=None):
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bounds: The bounding box of the viewport within which
            to bias geocode results more prominently.
        :type bounds: list or tuple

        :param string region: The region code, specified as a ccTLD
            ("top-level domain") two-character value.

        :param dict components: Restricts to an area. Can use any combination
            of: route, locality, administrative_area, postal_code, country.

        :param string language: The language in which to return results.

        :param bool sensor: Whether the geocoding request comes from a
            device with a location sensor.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call only,
            the value set during the geocoder's initialization.

        """
        params = {
            'address': self.format_string % query,
            'output': 'json',
            'ak': self.ak
        }

        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    def reverse(self, query, language=None, # pylint: disable=W0221,R0913
                    sensor=False, exactly_one=False, timeout=None):
        """
        Given a point, find an address.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param string language: The language in which to return results.

        :param boolean sensor: Whether the geocoding request comes from a
            device with a location sensor.

        :param boolean exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

        """
        params = {
            'ak': self.ak,
            'location': self._coerce_point_to_string(query),
            'output': 'json'
        }

        url = "?".join((self.api, urlencode(params)))

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_reverse_json(
            self._call_geocoder(url, timeout=timeout)
        )


    def _parse_reverse_json(self, page):
        place = page.get('result')

        location = place.get('formatted_address').encode('utf-8')
        latitude = place['location']['lat']
        longitude = place['location']['lng']

        return Location(location, (latitude, longitude), place)


    def _parse_json(self, page, exactly_one=True):
        '''Returns location, (latitude, longitude) from json feed.'''

        place = page.get('result', None)

        if not place:
            self._check_status(page.get('status'))
            return None

        def parse_place(place):
            '''Get the location, lat, lng from a single json place.'''
            location = place.get('level')
            latitude = place['location']['lat']
            longitude = place['location']['lng']
            return Location(location, (latitude, longitude), place)

        if exactly_one:
            return parse_place(place)
        else:
            return [parse_place(place) for place in places]

    @staticmethod
    def _check_status(status):
        """
        Validates error statuses.
        """
        print status
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
