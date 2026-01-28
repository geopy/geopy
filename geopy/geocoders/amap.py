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

__all__ = ("AMap", )


class AMap(Geocoder):
    """Geocoder using the AMap Maps Web Service API.

    Documentation at:
        https://lbs.amap.com/api/webservice/guide/api/georegeo

    """

    api_path = '/v3/geocode/geo'
    reverse_path = '/v3/geocode/regeo'

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
            console (https://console.amap.com/dev/key/app).

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
            (https://lbs.amap.com/api/javascript-api/guide/abc/prepare).
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
        self.api = '%s://restapi.amap.com%s' % (self.scheme, self.api_path)
        self.reverse_api = '%s://restapi.amap.com%s' % (self.scheme, self.reverse_path)
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
            'key': self.api_key,
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
        longlat = eval("[" + self._coerce_point_to_string(query) + "]")
        params = {
            'key': self.api_key,
            'output': 'json',
            'location': f'{longlat[1]},{longlat[0]}',
        }

        url = self._construct_url(self.reverse_api, self.reverse_path, params)

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_reverse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_reverse_json(self, page, exactly_one=True):
        """
        Parses a location from a single-result reverse API call.
        """
        place = page.get('regeocode')

        if not place:
            self._check_status(page.get('infocode'))
            return None

        location = place.get('formatted_address')
        longlat = eval("[" + place['addressComponent']['streetNumber']['location'] + "]")

        location = Location(location, (longlat[1], longlat[0]), place)
        if exactly_one:
            return location
        else:
            return [location]

    def _parse_json(self, page, exactly_one=True):
        """
        Returns location, (latitude, longitude) from JSON feed.
        """

        place = page.get('geocodes')[0]

        if not place:
            self._check_status(page.get('infocode'))
            return None

        def parse_place(place):
            """
            Get the location, lat, lng from a single JSON place.
            """
            location = place.get('level')
            longlat = eval("[" + place['location'] + "]")
            return Location(location, (longlat[1], longlat[0]), place)

        if exactly_one:
            return parse_place(place)
        else:
            return [parse_place(item) for item in place]

    def _check_status(self, status):
        """
        Validates error statuses.
        """
        if status == '10000':
            # When there are no results, just return.
            return
        if status == '10001':
            raise GeocoderAuthenticationFailure(
                'key不正确或过期.'
            )
        elif status == '10002':
            raise GeocoderServiceError(
                '没有权限使用相应的服务或者请求接口的路径拼写错误.'
            )
        elif status == '10003':
            raise GeocoderQuotaExceeded(
                '访问已超出日访问量.'
            )
        elif status == '10004':
            raise GeocoderServiceError(
                'IP白名单出错，发送请求的服务器IP不在IP白名单内.'
            )
        # MORE Error https://lbs.amap.com/api/webservice/guide/tools/info
        elif status == '10005':
            raise GeocoderServiceError(
                '没有权限使用相应的服务或者请求接口的路径拼写错误.'
            )
        else:
            raise GeocoderQueryError('Unknown error. Status: %r' % status)

    def _construct_url(self, url, path, params):
        query_string = urlencode(params)
        if self.security_key is None:
            return "%s?%s" % (url, query_string)
        else:
            # https://lbs.amap.com/api/javascript-api/guide/abc/prepare
            raw = "%s?%s%s" % (path, query_string, self.security_key)
            sn = hashlib.md5(quote_plus(raw).encode('utf-8')).hexdigest()
            return "%s?%s&sn=%s" % (url, query_string, sn)
