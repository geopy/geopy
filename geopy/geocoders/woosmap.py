import collections.abc
from functools import partial
from urllib.parse import urlencode

from geopy.exc import GeocoderQueryError, GeocoderServiceError, GeocoderUnavailable
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("Woosmap",)


class Woosmap(Geocoder):
    """Geocoder using the Woosmap Address API.

    Documentation at:
        https://developers.woosmap.com/products/address-api/geocode/

    .. versionadded:: 2.4
    """

    api_path = '/address/geocode/json'

    def __init__(
        self,
        api_key,
        *,
        domain='api.woosmap.com',
        scheme=None,
        timeout=DEFAULT_SENTINEL,
        proxies=DEFAULT_SENTINEL,
        user_agent=None,
        ssl_context=DEFAULT_SENTINEL,
        adapter_factory=None,
    ):
        """

        :param str api_key: The Private API key required by Woosmap to perform
            geocoding requests.
            API keys are managed through
            the Woosmap Console (https://console.woosmap.com/).
            Make sure to have ``Address API`` service enabled
            for your project Private API key.

        :param str domain: Domain where the target Woosmap service
            is hosted.

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
        self.api_key = api_key
        self.domain = domain.strip('/')
        self.api = '%s://%s%s' % (self.scheme, self.domain, self.api_path)

    def _format_components_param(self, components):
        component_items = []

        if isinstance(components, collections.abc.Mapping):
            component_items = components.items()
        elif (
            isinstance(components, collections.abc.Sequence)
            and not isinstance(components, (str, bytes))
        ):
            component_items = components
        else:
            raise ValueError(
                '`components` parameter must be of type `dict` or `list`')

        return "|".join(
            ":".join(item) for item in component_items
        )

    def geocode(
        self,
        query,
        *,
        limit=None,
        exactly_one=True,
        timeout=DEFAULT_SENTINEL,
        location=None,
        components=None,
        language=None,
        country_code_format=None,
    ):
        """
        Return a location point by address.

        :param str query: The address you wish to geocode.

        :param int limit: Maximum number of results to be returned.
            This will be reset to one if ``exactly_one`` is True.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :type location: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.
        :param location: The center latlng to bias the search context.

        :type components: dict or list
        :param components: Geographic places to which you would like to restrict
            your results. Currently, you can use components to filter over countries.
            Countries are identified by a two character, ISO 3166-1 Alpha-2
            or a three character, ISO 3166-1 Alpha-3 compatible country code.

            Pass a list of tuples if you want to specify multiple components of
            the same type, e.g.:

                >>> [('country', 'FRA'), ('country', 'DE')]

        :param str language: The language in which to return results.
            Must be a ISO 639-1 language code.

        :param str country_code_format: Default country code format
            in responses is Alpha3.
            However, format in responses can be changed
            by specifying components in alpha2.
            Available formats: ``alpha2``, ``alpha3``.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = {
            'address': query,
            'private_key': self.api_key,
        }

        if location:
            point = self._coerce_point_to_string(location,
                                                 output_format="%(lat)s,%(lon)s")
            params['location'] = point
        if components:
            params['components'] = self._format_components_param(components)
        if language:
            params['language'] = language
        if country_code_format:
            params['cc_format'] = country_code_format
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
        limit=None,
        exactly_one=True,
        timeout=DEFAULT_SENTINEL,
        language=None,
        country_code_format=None,
    ):
        """
        Return an address by location point.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param int limit: Maximum number of results to be returned.
            This will be reset to one if ``exactly_one`` is True.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param str language: The language in which to return results.

        :param str country_code_format: Default country code format
            in responses is Alpha3.
            However, format in responses can be changed
            by specifying components in alpha2.
            Available formats: ``alpha2``, ``alpha3``.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """

        latlng = self._coerce_point_to_string(query, output_format="%(lat)s,%(lon)s")
        params = {
            'latlng': latlng,
            'private_key': self.api_key,
        }
        if language:
            params['language'] = language
        if country_code_format:
            params['cc_format'] = country_code_format
        if limit:
            params['limit'] = limit
        if exactly_one:
            params['limit'] = 1

        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_json(self, response, exactly_one=True):
        addresses = response.get('results', [])

        self._check_status(response)
        if not addresses:
            return None

        def parse_address(address):
            """Get the location, lat, lng from a single json address."""
            location = address.get('formatted_address')
            latitude = address['geometry']['location']['lat']
            longitude = address['geometry']['location']['lng']
            return Location(location, (latitude, longitude), address)

        if exactly_one:
            return parse_address(addresses[0])
        else:
            return [parse_address(address) for address in addresses]

    def _check_status(self, response):
        # https://developers.woosmap.com/products/address-api/geocode/#status
        status = response.get('status')
        if status == 'OK':
            return
        if status == 'ZERO_RESULTS':
            return

        error_message = response.get('error_message')
        if status == 'INVALID_REQUEST':
            raise GeocoderQueryError(
                error_message or 'Invalid request or missing address or latlng')
        elif status == 'REQUEST_DENIED':
            raise GeocoderQueryError(
                error_message or 'Your request was denied. Please check your API Key')
        elif status == 'UNKNOWN_ERROR':
            raise GeocoderUnavailable(error_message or 'Server error')
        else:
            # Unknown (undocumented) status.
            raise GeocoderServiceError(error_message or 'Unknown error')
