import hashlib
from functools import partial
from urllib.parse import quote_plus, urlencode

from geopy.exc import (
    GeocoderAuthenticationFailure,
    GeocoderQueryError,
    GeocoderQuotaExceeded,
    GeocoderServiceError,
)
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("Baidu", "BaiduV3")


class Baidu(Geocoder):
    """Geocoder using the Baidu Maps v2 API.

    Documentation at:
        http://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-geocoding

    .. attention::
        Newly registered API keys will not work with v2 API,
        use :class:`.BaiduV3` instead.
    """

    api_path = '/geocoder/v2/'
    reverse_path = '/geocoder/v2/'

    def __init__(
            self,
            api_key,
            *,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None,
            security_key=None
    ):
        """

        :param str api_key: The API key (AK) required by Baidu Map to perform
            geocoding requests. API keys are managed through the Baidu APIs
            console (http://lbsyun.baidu.com/apiconsole/key).

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str user_agent:
            See :attr:`geopy.geocoders.options.default_user_agent`.

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.

        :param callable adapter_factory:
            See :attr:`geopy.geocoders.options.default_adapter_factory`.

            .. versionadded:: 2.0

        :param str security_key: The security key (SK) to calculate
            the SN parameter in request if authentication setting requires
            (http://lbsyun.baidu.com/index.php?title=lbscloud/api/appendix).
        """
        super().__init__(
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )
        self.api_key = api_key
        self.api = '%s://api.map.baidu.com%s' % (self.scheme, self.api_path)
        self.reverse_api = '%s://api.map.baidu.com%s' % (self.scheme, self.reverse_path)
        self.security_key = security_key

    def _format_components_param(self, components):
        """
        Format the components dict to something Baidu understands.
        """
        return "|".join(
            (":".join(item) for item in components.items())
        )

    def geocode(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """
        params = {
            'ak': self.api_key,
            'output': 'json',
            'address': query,
        }

        url = self._construct_url(self.api, self.api_path, params)

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(self, query, *, exactly_one=True, timeout=DEFAULT_SENTINEL):
        """
        Return an address by location point.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param bool exactly_one: Return one result or a list of results, if
            available. Baidu's API will always return at most one result.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """
        params = {
            'ak': self.api_key,
            'output': 'json',
            'location': self._coerce_point_to_string(query),
        }

        url = self._construct_url(self.reverse_api, self.reverse_path, params)

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_reverse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_reverse_json(self, page, exactly_one=True):
        """
        Parses a location from a single-result reverse API call.
        """
        place = page.get('result')

        if not place:
            self._check_status(page.get('status'))
            return None

        location = place.get('formatted_address').encode('utf-8')
        latitude = place['location']['lat']
        longitude = place['location']['lng']

        location = Location(location, (latitude, longitude), place)
        if exactly_one:
            return location
        else:
            return [location]

    def _parse_json(self, page, exactly_one=True):
        """
        Returns location, (latitude, longitude) from JSON feed.
        """

        place = page.get('result')

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

    def _check_status(self, status):
        """
        Validates error statuses.
        """
        if status == 0:
            # When there are no results, just return.
            return
        if status == 1:
            raise GeocoderServiceError(
                'Internal server error.'
            )
        elif status == 2:
            raise GeocoderQueryError(
                'Invalid request.'
            )
        elif status == 3:
            raise GeocoderAuthenticationFailure(
                'Authentication failure.'
            )
        elif status == 4:
            raise GeocoderQuotaExceeded(
                'Quota validate failure.'
            )
        elif status == 5:
            raise GeocoderQueryError(
                'AK Illegal or Not Exist.'
            )
        elif status == 101:
            raise GeocoderAuthenticationFailure(
                'No AK'
            )
        elif status == 102:
            raise GeocoderAuthenticationFailure(
                'MCODE Error'
            )
        elif status == 200:
            raise GeocoderAuthenticationFailure(
                'Invalid AK'
            )
        elif status == 211:
            raise GeocoderAuthenticationFailure(
                'Invalid SN'
            )
        elif 200 <= status < 300:
            raise GeocoderAuthenticationFailure(
                'Authentication Failure'
            )
        elif 300 <= status < 500:
            raise GeocoderQuotaExceeded(
                'Quota Error.'
            )
        else:
            raise GeocoderQueryError('Unknown error. Status: %r' % status)

    def _construct_url(self, url, path, params):
        query_string = urlencode(params)
        if self.security_key is None:
            return "%s?%s" % (url, query_string)
        else:
            # http://lbsyun.baidu.com/index.php?title=lbscloud/api/appendix
            raw = "%s?%s%s" % (path, query_string, self.security_key)
            sn = hashlib.md5(quote_plus(raw).encode('utf-8')).hexdigest()
            return "%s?%s&sn=%s" % (url, query_string, sn)


class BaiduV3(Baidu):
    """Geocoder using the Baidu Maps v3 API.

    Documentation at:
        http://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-geocoding
    """

    api_path = '/geocoding/v3/'
    reverse_path = '/reverse_geocoding/v3/'
