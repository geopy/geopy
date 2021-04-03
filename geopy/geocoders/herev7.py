import json
from functools import partial
from urllib.parse import urlencode

from geopy.adapters import AdapterHTTPError
from geopy.exc import GeocoderQueryError, GeocoderServiceError
from geopy.geocoders.base import DEFAULT_SENTINEL, ERROR_CODE_MAP, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("HereV7", )


class HereV7(Geocoder):
    """Geocoder using the HERE Geocoding & Search v7 API.

    Documentation at:
        https://developer.here.com/documentation/geocoding-search-api/

    Terms of Service at:
        https://legal.here.com/en-gb/terms
    """

    structured_query_params = {
        'country',
        'state',
        'county',
        'city',
        'district',
        'street',
        'houseNumber',
        'postalCode',
    }

    geocode_path = '/v1/geocode'
    reverse_path = '/v1/revgeocode'

    def __init__(
            self,
            apikey,
            *,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """

        :param str apikey: Should be a valid HERE Maps apikey.
            A project can be created at
            https://developer.here.com/projects.

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
        """
        super().__init__(
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )

        domain = "search.hereapi.com"

        self.apikey = apikey
        self.api = "%s://geocode.%s%s" % (self.scheme, domain, self.geocode_path)
        self.reverse_api = (
            "%s://revgeocode.%s%s" % (self.scheme, domain, self.reverse_path)
        )

    def geocode(
        self,
        query=None,
        *,
        components=None,
        at=None,
        countries=None,
        language=None,
        limit=None,
        exactly_one=True,
        timeout=DEFAULT_SENTINEL
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode. Optional,
            if ``components`` param is set.

        :param dict components: A structured query. Can be used along with
            the free-text ``query``. Should be a dictionary whose keys
            are one of:
            `country`, `state`, `county`, `city`, `district`, `street`,
            `houseNumber`, `postalCode`.

        :param at: The center of the search context.
        :type at: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param list countries: A list of country codes specified in
            `ISO 3166-1 alpha-3 <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3>`_
            format, e.g. ``['USA', 'CAN']``.
            This is a hard filter.

        :param str language: Affects the language of the response,
            must be a BCP 47 compliant language code, e.g. ``en-US``.

        :param int limit: Defines the maximum number of items in the
            response structure. If not provided and there are multiple results
            the HERE API will return 20 results by default. This will be reset
            to one if ``exactly_one`` is True.

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
            'apiKey': self.apikey,
        }

        if query:
            params['q'] = query

        if components:
            parts = [
                "{}={}".format(key, val)
                for key, val
                in components.items()
                if key in self.structured_query_params
            ]
            if not parts:
                raise GeocoderQueryError("`components` dict must not be empty")
            for pair in parts:
                if ';' in pair:
                    raise GeocoderQueryError(
                        "';' must not be used in values of the structured query. "
                        "Offending pair: {!r}".format(pair)
                    )
            params['qq'] = ';'.join(parts)

        if at:
            point = self._coerce_point_to_string(at, output_format="%(lat)s,%(lon)s")
            params['at'] = point

        if countries:
            params['in'] = 'countryCode:' + ','.join(countries)

        if language:
            params['lang'] = language

        if limit:
            params['limit'] = limit
        if exactly_one:
            params['limit'] = 1

        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(
            self,
            query,
            *,
            language=None,
            limit=None,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return an address by location point.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param str language: Affects the language of the response,
            must be a BCP 47 compliant language code, e.g. ``en-US``.

        :param int limit: Maximum number of results to be returned.
            This will be reset to one if ``exactly_one`` is True.

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
            'at': self._coerce_point_to_string(query, output_format="%(lat)s,%(lon)s"),
            'apiKey': self.apikey,
        }

        if language:
            params['lang'] = language

        if limit:
            params['limit'] = limit
        if exactly_one:
            params['limit'] = 1

        url = "%s?%s" % (self.reverse_api, urlencode(params))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_json(self, doc, exactly_one=True):
        resources = doc['items']
        if not resources:
            return None

        def parse_resource(resource):
            """
            Parse each return object.
            """
            location = resource['title']
            position = resource['position']

            latitude, longitude = position['lat'], position['lng']

            return Location(location, (latitude, longitude), resource)

        if exactly_one:
            return parse_resource(resources[0])
        else:
            return [parse_resource(resource) for resource in resources]

    def _geocoder_exception_handler(self, error):
        if not isinstance(error, AdapterHTTPError):
            return
        if error.status_code is None or error.text is None:
            return
        try:
            body = json.loads(error.text)
        except ValueError:
            message = error.text
        else:
            # `title`: https://developer.here.com/documentation/geocoding-search-api/api-reference-swagger.html  # noqa
            # `error_description`: returned for queries without apiKey.
            message = body.get('title') or body.get('error_description') or error.text
        exc_cls = ERROR_CODE_MAP.get(error.status_code, GeocoderServiceError)
        raise exc_cls(message) from error
