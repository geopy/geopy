from geopy.compat import urlencode
from geopy.exc import ConfigurationError, GeocoderQuotaExceeded
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("LiveAddress", )


class LiveAddress(Geocoder):
    """Geocoder using the LiveAddress API provided by SmartyStreets.

    Documentation at:
        https://smartystreets.com/docs/cloud/us-street-api
    """

    geocode_path = '/street-address'

    def __init__(
            self,
            auth_id,
            auth_token,
            candidates=1,
            scheme='https',
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            format_string=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """

        :param str auth_id: Valid `Auth ID` from SmartyStreets.

            .. versionadded:: 1.5.0

        :param str auth_token: Valid `Auth Token` from SmartyStreets.

        :param int candidates: An integer between 1 and 10 indicating the max
            number of candidate addresses to return if a valid address
            could be found.

        :param str scheme: Must be ``https``.

            .. deprecated:: 1.14.0
               Don't use this parameter, it's going to be removed in
               geopy 2.0.

            .. versionchanged:: 1.8.0
               LiveAddress now requires `https`. Specifying `scheme=http` will
               result in a :class:`geopy.exc.ConfigurationError`.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str user_agent:
            See :attr:`geopy.geocoders.options.default_user_agent`.

            .. versionadded:: 1.12.0

        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

            .. versionadded:: 1.14.0

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.

            .. versionadded:: 1.14.0
        """
        super(LiveAddress, self).__init__(
            format_string=format_string,
            # The `scheme` argument is present for the legacy reasons only.
            # If a custom value has been passed, it should be validated.
            # Otherwise use `https` instead of the `options.default_scheme`.
            scheme=(scheme or 'https'),
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )
        if self.scheme != "https":
            raise ConfigurationError("LiveAddress now requires `https`.")
        self.auth_id = auth_id
        self.auth_token = auth_token
        if candidates:
            if not (1 <= candidates <= 10):
                raise ValueError('candidates must be between 1 and 10')
        self.candidates = candidates
        domain = 'api.smartystreets.com'
        self.api = '%s://%s%s' % (self.scheme, domain, self.geocode_path)

    def geocode(self, query, exactly_one=True, timeout=DEFAULT_SENTINEL):
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
        url = self._compose_url(self.format_string % query)
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(self._call_geocoder(url, timeout=timeout),
                                exactly_one)

    def _geocoder_exception_handler(self, error, message):
        """
        LiveStreets-specific exceptions.
        """
        if "no active subscriptions found" in message.lower():
            raise GeocoderQuotaExceeded(message)

    def _compose_url(self, location):
        """
        Generate API URL.
        """
        query = {
            'auth-id': self.auth_id,
            'auth-token': self.auth_token,
            'street': location,
            'candidates': self.candidates
        }
        return '{url}?{query}'.format(url=self.api, query=urlencode(query))

    def _parse_json(self, response, exactly_one=True):
        """
        Parse responses as JSON objects.
        """
        if not len(response):
            return None
        if exactly_one:
            return self._format_structured_address(response[0])
        else:
            return [self._format_structured_address(c) for c in response]

    @staticmethod
    def _format_structured_address(address):
        """
        Pretty-print address and return lat, lon tuple.
        """
        latitude = address['metadata'].get('latitude')
        longitude = address['metadata'].get('longitude')
        return Location(
            ", ".join((address['delivery_line_1'], address['last_line'])),
            (latitude, longitude) if latitude and longitude else None,
            address
        )
