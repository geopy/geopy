from functools import partial
from urllib.parse import urlencode

from geopy.adapters import AdapterHTTPError
from geopy.exc import GeocoderQuotaExceeded
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
            *,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """

        :param str auth_id: Valid `Auth ID` from SmartyStreets.

        :param str auth_token: Valid `Auth Token` from SmartyStreets.

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
            scheme='https',
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )
        self.auth_id = auth_id
        self.auth_token = auth_token

        domain = 'api.smartystreets.com'
        self.api = '%s://%s%s' % (self.scheme, domain, self.geocode_path)

    def geocode(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            candidates=1
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

        :param int candidates: An integer between 1 and 10 indicating the max
            number of candidate addresses to return if a valid address
            could be found.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """

        if not (1 <= candidates <= 10):
            raise ValueError('candidates must be between 1 and 10')

        query = {
            'auth-id': self.auth_id,
            'auth-token': self.auth_token,
            'street': query,
            'candidates': candidates,
        }
        url = '{url}?{query}'.format(url=self.api, query=urlencode(query))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _geocoder_exception_handler(self, error):
        search = "no active subscriptions found"
        if isinstance(error, AdapterHTTPError):
            if search in str(error).lower():
                raise GeocoderQuotaExceeded(str(error)) from error
            if search in (error.text or "").lower():
                raise GeocoderQuotaExceeded(error.text) from error

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

    def _format_structured_address(self, address):
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
