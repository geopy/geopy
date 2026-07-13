from functools import partial
from urllib.parse import urlencode

from geopy.exc import (
    GeocoderAuthenticationFailure,
    GeocoderQueryError,
    GeocoderQuotaExceeded,
    GeocoderServiceError,
)
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("Ip2geo",)


class Ip2geo(Geocoder):
    """Geocoder using the ip2geo IP geolocation service.

    Documentation at:
        https://ip2geo.dev/docs

    .. versionadded:: 2.5
    """

    geocode_path = '/convert'

    def __init__(
            self,
            api_key,
            *,
            domain='api.ip2geo.dev',
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """

        :param str api_key: The API key required by ip2geo
            to perform geocoding requests. You can get your key here:
            https://ip2geo.dev

        :param str domain: Domain where the target ip2geo service
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
        self.api = '%s://%s%s' % (self.scheme, self.domain,
                                  self.geocode_path)

    def geocode(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return a location for the given IP address.

        :param str query: The IP address you wish to geolocate.

        :param bool exactly_one: Return one result or a list of
            results, if available. ip2geo always returns a single
            result per IP address.

        :param int timeout: Time, in seconds, to wait for the
            geocoding service to respond before raising a
            :class:`geopy.exc.GeocoderTimedOut` exception. Set this
            only if you wish to override, on this call only, the
            value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a
            list of them, if ``exactly_one=False``.
        """
        params = {
            'ip': query,
        }

        url = "?".join((self.api, urlencode(params)))

        logger.debug(
            "%s.geocode: %s", self.__class__.__name__, url
        )
        callback = partial(
            self._parse_json, exactly_one=exactly_one
        )
        return self._call_geocoder(
            url,
            callback,
            timeout=timeout,
            headers={'X-Api-Key': self.api_key},
        )

    def _parse_json(self, page, exactly_one=True):
        self._check_status(page)

        data = page.get('data')
        if not data:
            return None

        location = self._parse_location(data)

        if exactly_one:
            return location
        else:
            return [location]

    def _parse_location(self, data):
        continent = data.get('continent') or {}
        country = continent.get('country') or {}
        city = country.get('city') or {}
        subdivision = country.get('subdivision') or {}

        city_name = city.get('name') or ''
        state_name = subdivision.get('name') or ''
        country_name = country.get('name') or ''

        parts = [p for p in (city_name, state_name,
                             country_name) if p]
        address = ', '.join(parts)

        latitude = city.get('latitude')
        longitude = city.get('longitude')

        point = (latitude, longitude) if latitude and longitude \
            else None

        return Location(address, point, data)

    def _check_status(self, page):
        success = page.get('success')
        if success:
            return

        code = page.get('code', 0)
        message = page.get('message', 'Unknown error')

        if code == 401:
            raise GeocoderAuthenticationFailure(message)
        elif code == 429:
            raise GeocoderQuotaExceeded(message)
        elif code == 400:
            raise GeocoderQueryError(message)
        else:
            raise GeocoderServiceError(message)
