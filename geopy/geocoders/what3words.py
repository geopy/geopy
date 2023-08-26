import re
from functools import partial
from urllib.parse import urlencode

from geopy import exc
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("What3Words", "What3WordsV3")

_MULTIPLE_WORD_RE = re.compile(
    r"[^\W\d\_]+\.{1,1}[^\W\d\_]+\.{1,1}[^\W\d\_]+$", re.U
)


def _check_query(query):
    """
    Check query validity with regex
    """
    if not _MULTIPLE_WORD_RE.match(query):
        return False
    else:
        return True


class What3Words(Geocoder):
    """What3Words geocoder using the legacy V2 API.

    Documentation at:
        https://docs.what3words.com/api/v2/

    .. attention::
        Consider using :class:`.What3WordsV3` instead.
    """

    geocode_path = '/v2/forward'
    reverse_path = '/v2/reverse'

    def __init__(
            self,
            api_key,
            *,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None,
            domain='api.what3words.com',
    ):
        """

        :param str api_key: Key provided by What3Words
            (https://accounts.what3words.com/register).

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

        :param str domain: base api domain

            .. versionadded:: 2.4
        """
        super().__init__(
            scheme='https',
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )

        self.api_key = api_key
        self.geocode_api = '%s://%s%s' % (self.scheme, domain, self.geocode_path)
        self.reverse_api = '%s://%s%s' % (self.scheme, domain, self.reverse_path)

    def geocode(
            self,
            query,
            *,
            lang='en',
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):

        """
        Return a location point for a `3 words` query. If the `3 words` address
        doesn't exist, a :class:`geopy.exc.GeocoderQueryError` exception will be
        thrown.

        :param str query: The 3-word address you wish to geocode.

        :param str lang: two character language code as supported by
            the API (https://docs.what3words.com/api/v2/#lang).

        :param bool exactly_one: Return one result or a list of results, if
            available. Due to the address scheme there is always exactly one
            result for each `3 words` address, so this parameter is rather
            useless for this geocoder.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """

        if not _check_query(query):
            raise exc.GeocoderQueryError(
                "Search string must be 'word.word.word'"
            )

        params = {
            'addr': query,
            'lang': lang.lower(),
            'key': self.api_key,
        }

        url = "?".join((self.geocode_api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_json(self, resources, exactly_one=True):
        """
        Parse type, words, latitude, and longitude and language from a
        JSON response.
        """

        code = resources['status'].get('code')

        if code:
            # https://docs.what3words.com/api/v2/#errors
            exc_msg = "Error returned by What3Words: %s" % resources['status']['message']
            if code == 401:
                raise exc.GeocoderAuthenticationFailure(exc_msg)

            raise exc.GeocoderQueryError(exc_msg)

        def parse_resource(resource):
            """
            Parse record.
            """

            if 'geometry' in resource:
                words = resource['words']
                position = resource['geometry']
                latitude, longitude = position['lat'], position['lng']
                if latitude and longitude:
                    latitude = float(latitude)
                    longitude = float(longitude)

                return Location(words, (latitude, longitude), resource)
            else:
                raise exc.GeocoderParseError('Error parsing result.')

        location = parse_resource(resources)
        if exactly_one:
            return location
        else:
            return [location]

    def reverse(
            self,
            query,
            *,
            lang='en',
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return a `3 words` address by location point. Each point on surface has
        a `3 words` address, so there's always a non-empty response.

        :param query: The coordinates for which you wish to obtain the 3 word
            address.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param str lang: two character language code as supported by the
            API (https://docs.what3words.com/api/v2/#lang).

        :param bool exactly_one: Return one result or a list of results, if
            available. Due to the address scheme there is always exactly one
            result for each `3 words` address, so this parameter is rather
            useless for this geocoder.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """
        lang = lang.lower()

        params = {
            'coords': self._coerce_point_to_string(query),
            'lang': lang.lower(),
            'key': self.api_key,
        }

        url = "?".join((self.reverse_api, urlencode(params)))

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_reverse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_reverse_json(self, resources, exactly_one=True):
        """
        Parses a location from a single-result reverse API call.
        """
        return self._parse_json(resources, exactly_one)


class What3WordsV3(Geocoder):
    """What3Words geocoder using the V3 API.

    Documentation at:
        https://developer.what3words.com/public-api/docs

    .. versionadded:: 2.2
    """

    geocode_path = '/v3/convert-to-coordinates'
    reverse_path = '/v3/convert-to-3wa'

    def __init__(
            self,
            api_key,
            *,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None,
            domain='api.what3words.com',
    ):
        """

        :param str api_key: Key provided by What3Words
            (https://accounts.what3words.com/register).

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

        :param str domain: base api domain

            .. versionadded:: 2.4
        """
        super().__init__(
            scheme='https',
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )

        self.api_key = api_key
        self.geocode_api = '%s://%s%s' % (self.scheme, domain, self.geocode_path)
        self.reverse_api = '%s://%s%s' % (self.scheme, domain, self.reverse_path)

    def geocode(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):

        """
        Return a location point for a `3 words` query. If the `3 words` address
        doesn't exist, a :class:`geopy.exc.GeocoderQueryError` exception will be
        thrown.

        :param str query: The 3-word address you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available. Due to the address scheme there is always exactly one
            result for each `3 words` address, so this parameter is rather
            useless for this geocoder.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """

        if not _check_query(query):
            raise exc.GeocoderQueryError(
                "Search string must be 'word.word.word'"
            )

        params = {
            'words': query,
            'key': self.api_key,
        }

        url = "?".join((self.geocode_api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_json(self, resources, exactly_one=True):
        """
        Parse type, words, latitude, and longitude and language from a
        JSON response.
        """

        error = resources.get('error')

        if error is not None:
            # https://developer.what3words.com/public-api/docs#error-handling
            exc_msg = "Error returned by What3Words: %s" % resources["error"]["message"]
            exc_code = error.get('code')
            if exc_code in ['MissingKey', 'InvalidKey']:
                raise exc.GeocoderAuthenticationFailure(exc_msg)

            raise exc.GeocoderQueryError(exc_msg)

        def parse_resource(resource):
            """
            Parse record.
            """

            if 'coordinates' in resource:
                words = resource['words']
                position = resource['coordinates']
                latitude, longitude = position['lat'], position['lng']
                if latitude and longitude:
                    latitude = float(latitude)
                    longitude = float(longitude)

                return Location(words, (latitude, longitude), resource)
            else:
                raise exc.GeocoderParseError('Error parsing result.')

        location = parse_resource(resources)
        if exactly_one:
            return location
        else:
            return [location]

    def reverse(
            self,
            query,
            *,
            lang='en',
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return a `3 words` address by location point. Each point on surface has
        a `3 words` address, so there's always a non-empty response.

        :param query: The coordinates for which you wish to obtain the 3 word
            address.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param str lang: two character language code as supported by the
            API (https://developer.what3words.com/public-api/docs#available-languages).

        :param bool exactly_one: Return one result or a list of results, if
            available. Due to the address scheme there is always exactly one
            result for each `3 words` address, so this parameter is rather
            useless for this geocoder.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """
        lang = lang.lower()

        params = {
            'coordinates': self._coerce_point_to_string(query),
            'language': lang.lower(),
            'key': self.api_key,
        }

        url = "?".join((self.reverse_api, urlencode(params)))

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_reverse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_reverse_json(self, resources, exactly_one=True):
        """
        Parses a location from a single-result reverse API call.
        """
        return self._parse_json(resources, exactly_one)
