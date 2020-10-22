import collections.abc
from functools import partial
from urllib.parse import urlencode

from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import join_filter, logger

__all__ = ("Geolake", )


class Geolake(Geocoder):
    """Geocoder using the Geolake API.

    Documentation at:
        https://geolake.com/docs/api

    Terms of Service at:
        https://geolake.com/terms-of-use
    """

    structured_query_params = {
        'country',
        'state',
        'city',
        'zipcode',
        'street',
        'address',
        'houseNumber',
        'subNumber',
    }

    api_path = '/v1/geocode'

    def __init__(
            self,
            api_key,
            *,
            domain='api.geolake.com',
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """

        :param str api_key: The API key required by Geolake
            to perform geocoding requests. You can get your key here:
            https://geolake.com/

        :param str domain: Currently it is ``'api.geolake.com'``, can
            be changed for testing purposes.

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

    def geocode(
            self,
            query,
            *,
            country_codes=None,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

            For a structured query, provide a dictionary whose keys
            are one of: `country`, `state`, `city`, `zipcode`, `street`, `address`,
            `houseNumber` or `subNumber`.

        :param country_codes: Provides the geocoder with a list
            of country codes that the query may reside in. This value will
            limit the geocoder to the supplied countries. The country code
            is a 2 character code as defined by the ISO-3166-1 alpha-2
            standard (e.g. ``FR``). Multiple countries can be specified with
            a Python list.

        :type country_codes: str or list

        :param bool exactly_one: Return one result or a list of one result.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """

        if isinstance(query, collections.abc.Mapping):
            params = {
                key: val
                for key, val
                in query.items()
                if key in self.structured_query_params
            }
            params['api_key'] = self.api_key
        else:
            params = {
                'api_key': self.api_key,
                'q': query,
            }

        if not country_codes:
            country_codes = []
        if isinstance(country_codes, str):
            country_codes = [country_codes]
        if country_codes:
            params['countryCodes'] = ",".join(country_codes)

        url = "?".join((self.api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_json(self, page, exactly_one):
        """Returns location, (latitude, longitude) from json feed."""

        if not page.get('success'):
            return None

        latitude = page['latitude']
        longitude = page['longitude']

        address = self._get_address(page)
        result = Location(address, (latitude, longitude), page)
        if exactly_one:
            return result
        else:
            return [result]

    def _get_address(self, page):
        """
        Returns address string from page dictionary
        :param page: dict
        :return: str
        """
        place = page.get('place')
        address_city = place.get('city')
        address_country_code = place.get('countryCode')
        address = join_filter(', ', [address_city, address_country_code])
        return address
