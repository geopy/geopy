from geopy.compat import urlencode
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("Geolake", )


class Geolake(Geocoder):
    """Geocoder using the Geolake API.

    Documentation at:
        https://geolake.com/docs/api

    Terms of Service at:
        https://geolake.com/terms-of-use

    .. versionadded:: 1.18.0
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
            domain='api.geolake.com',
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            format_string=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """

        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

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

        """
        super(Geolake, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )

        self.api_key = api_key
        self.domain = domain.strip('/')
        self.api = '%s://%s%s' % (self.scheme, self.domain, self.api_path)

    def geocode(
            self,
            query,
            country_codes=None,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

            For a structured query, provide a dictionary whose keys
            are one of: `country`, `state`, `city`, `zipcode`, `street`, `address`,
            `houseNumber` or `subNumber`.

         :param str country_codes: Provides the geocoder with a list of country codes
            that the query may reside in. This value will limit the geocoder to the
            supplied countries. Te country code is a 2 character code as defined by
            the ISO-3166-1 alpha-2 standard.


        :param bool exactly_one: Return one result or a list of one result.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """

        if isinstance(query, dict):
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
                'q': self.format_string % query,
            }

        if country_codes is None:
            country_codes = []

        if len(country_codes):
            params['countryCodes'] = ",".join(country_codes)

        url = "?".join((self.api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    def _parse_json(self, page, exactly_one):
        """Returns location, (latitude, longitude) from json feed."""

        if not page.get('success'):
            return None

        latitude = page['latitude']
        longitude = page['longitude']

        place = page.get('place')
        address = ", ".join([place['city'], place['countryCode']])
        result = Location(address, (latitude, longitude), page)
        if exactly_one:
            return result
        else:
            return [result]
