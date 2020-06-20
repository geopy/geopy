from functools import partial
from urllib.parse import quote, urlencode

from geopy.adapters import AdapterHTTPError
from geopy.exc import GeocoderQuotaExceeded
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("TomTom", )


class TomTom(Geocoder):
    """TomTom geocoder.

    Documentation at:
        https://developer.tomtom.com/search-api/search-api-documentation
    """

    geocode_path = '/search/2/geocode/%(query)s.json'
    reverse_path = '/search/2/reverseGeocode/%(position)s.json'

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
            domain='api.tomtom.com'
    ):
        """
        :param str api_key: TomTom API key.

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

        :param str domain: Domain where the target TomTom service
            is hosted.
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
        self.api = "%s://%s%s" % (self.scheme, domain, self.geocode_path)
        self.api_reverse = "%s://%s%s" % (self.scheme, domain, self.reverse_path)

    def geocode(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            limit=None,
            typeahead=False,
            language=None
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

        :param int limit: Maximum amount of results to return from the service.
            Unless exactly_one is set to False, limit will always be 1.

        :param bool typeahead: If the "typeahead" flag is set, the query
            will be interpreted as a partial input and the search will
            enter predictive mode.

        :param str language: Language in which search results should be
            returned. When data in specified language is not
            available for a specific field, default language is used.
            List of supported languages (case-insensitive):
            https://developer.tomtom.com/online-search/online-search-documentation/supported-languages

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = self._geocode_params(query)
        params['typeahead'] = self._boolean_value(typeahead)

        if limit:
            params['limit'] = str(int(limit))
        if exactly_one:
            params['limit'] = '1'

        if language:
            params['language'] = language

        quoted_query = quote(query.encode('utf-8'))
        url = "?".join((self.api % dict(query=quoted_query),
                        urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            language=None
    ):
        """
        Return an address by location point.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param str language: Language in which search results should be
            returned. When data in specified language is not
            available for a specific field, default language is used.
            List of supported languages (case-insensitive):
            https://developer.tomtom.com/online-search/online-search-documentation/supported-languages

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        position = self._coerce_point_to_string(query)
        params = self._reverse_params(position)

        if language:
            params['language'] = language

        quoted_position = quote(position.encode('utf-8'))
        url = "?".join((self.api_reverse % dict(position=quoted_position),
                        urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_reverse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _boolean_value(self, bool_value):
        return 'true' if bool_value else 'false'

    def _geocode_params(self, formatted_query):
        return {
            'key': self.api_key,
        }

    def _reverse_params(self, position):
        return {
            'key': self.api_key,
        }

    def _parse_json(self, resources, exactly_one):
        if not resources or not resources['results']:
            return None

        if exactly_one:
            return self._parse_search_result(resources['results'][0])
        else:
            return [self._parse_search_result(result)
                    for result in resources['results']]

    def _parse_search_result(self, result):
        latitude = result['position']['lat']
        longitude = result['position']['lon']
        return Location(result['address']['freeformAddress'],
                        (latitude, longitude), result)

    def _parse_reverse_json(self, resources, exactly_one):
        if not resources or not resources['addresses']:
            return None

        if exactly_one:
            return self._parse_reverse_result(resources['addresses'][0])
        else:
            return [self._parse_reverse_result(result)
                    for result in resources['addresses']]

    def _parse_reverse_result(self, result):
        latitude, longitude = result['position'].split(',')
        return Location(result['address']['freeformAddress'],
                        (latitude, longitude), result)

    def _geocoder_exception_handler(self, error):
        if not isinstance(error, AdapterHTTPError):
            return
        if error.status_code is None or error.text is None:
            return
        if error.status_code >= 400 and "Developer Over Qps" in error.text:
            raise GeocoderQuotaExceeded("Developer Over Qps") from error
