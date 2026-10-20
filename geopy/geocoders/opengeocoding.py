from functools import partial
from urllib.parse import urlencode

from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("OpenGeocoding", )


class OpenGeocoding(Geocoder):
    """Geocoder using the OpenGeocoding API.

    Documentation at:
        https://opengeocoding.com/docs

    .. versionadded:: 2.6
    """

    geocode_path = '/v1/search'
    reverse_path = '/v1/reverse'

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
            domain='api.opengeocoding.com'
    ):
        """
        :param str api_key: The API key required by OpenGeocoding to perform
            geocoding requests. Create one in the dashboard at
            https://opengeocoding.com/dashboard.

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

        :param str domain: Base API domain for OpenGeocoding.
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
        self.geocode_api = '%s://%s%s' % (self.scheme, self.domain, self.geocode_path)
        self.reverse_api = '%s://%s%s' % (self.scheme, self.domain, self.reverse_path)

    def geocode(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return a location point by address.

        OpenGeocoding returns at most one result per query. The raw result
        contains ``goodMatch``, which is ``False`` or absent for a partial
        match (for example, a street found without the requested house
        number).

        :param str query: The address or place you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        url = '?'.join((self.geocode_api, urlencode({'addressString': query})))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_geocode, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout,
                                   headers=self._auth_headers())

    def reverse(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            radius=None,
            limit=None
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

        :param int radius: Search radius in metres. The service uses 500
            when it is omitted.

        :param int limit: Maximum number of results to return when
            ``exactly_one=False``. The service returns one result when it is
            omitted.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        lat, lon = self._coerce_point_to_string(query).split(',')
        params = {'lat': lat, 'lon': lon}
        if radius is not None:
            params['radiusM'] = int(radius)
        if exactly_one:
            params['size'] = 1
        elif limit is not None:
            params['size'] = int(limit)
        url = '?'.join((self.reverse_api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_reverse, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout,
                                   headers=self._auth_headers())

    def _auth_headers(self):
        # The service rejects keys in the URL so they don't end up in logs.
        return {'x-api-key': self.api_key}

    def _parse_address(self, address, raw):
        coordinates = address.get('geoCoordinates')
        if not coordinates:
            return None
        return Location(
            address.get('displayName'),
            (coordinates.get('lat', 0.0), coordinates.get('lon', 0.0)),
            raw,
        )

    def _parse_geocode(self, response, exactly_one):
        location = self._parse_address(response or {}, response)
        if location is None:
            return None
        return location if exactly_one else [location]

    def _parse_reverse(self, response, exactly_one):
        locations = [
            location
            for location in (
                self._parse_address(result.get('address') or {}, result)
                for result in (response or {}).get('results', [])
            )
            if location is not None
        ]
        if not locations:
            return None
        return locations[0] if exactly_one else locations
