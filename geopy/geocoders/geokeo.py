from functools import partial
from urllib.parse import urlencode

from geopy.exc import (
    GeocoderAuthenticationFailure,
    GeocoderQueryError,
    GeocoderQuotaExceeded,
    GeocoderServiceError,
    GeocoderUnavailable,
)
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("Geokeo", )


class Geokeo(Geocoder):
    """Geocoder using the geokeo API.

    Documentation at:
        https://geokeo.com/documentation.php

    .. versionadded:: 2.4
    """

    geocode_path = '/geocode/v1/search.php'
    reverse_path = '/geocode/v1/reverse.php'

    def __init__(
            self,
            api_key,
            *,
            domain='geokeo.com',
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """

        :param str api_key: The API key required by Geokeo.com
            to perform geocoding requests. You can get your key here:
            https://geokeo.com/

        :param str domain: Domain where the target Geokeo service
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
        self.api = '%s://%s%s' % (self.scheme, self.domain, self.geocode_path)
        self.reverse_api = '%s://%s%s' % (self.scheme, self.domain, self.reverse_path)

    def geocode(
            self,
            query,
            *,
            country=None,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

        :param str country: Restricts the results to the specified
            country. The country code is a 2 character code as
            defined by the ISO 3166-1 Alpha 2 standard (e.g. ``us``).

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
            'api': self.api_key,
            'q': query,
        }

        if country:
            params['country'] = country

        url = "?".join((self.api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
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

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """

        try:
            lat, lng = self._coerce_point_to_string(query).split(',')
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")

        params = {
            'api': self.api_key,
            'lat': lat,
            'lng': lng
        }

        url = "?".join((self.reverse_api, urlencode(params)))

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_json(self, page, exactly_one=True):
        places = page.get('results', [])
        self._check_status(page)
        if not places:
            return None

        def parse_place(place):
            '''Get the location, lat, lng from a single json place.'''
            location = place.get('formatted_address')
            latitude = place['geometry']['location']['lat']
            longitude = place['geometry']['location']['lng']
            return Location(location, (latitude, longitude), place)

        if exactly_one:
            return parse_place(places[0])
        else:
            return [parse_place(place) for place in places]

    def _check_status(self, page):
        status = (page.get("status") or "").upper()

        # https://geokeo.com/documentation.php#responsecodes
        if status == "OK":
            return
        if status == 'ZERO_RESULTS':
            return

        if status == 'INVALID_REQUEST':
            raise GeocoderQueryError('Invalid request parameters')
        elif status == "ACCESS_DENIED":
            raise GeocoderAuthenticationFailure('Access denied')
        elif status == "OVER_QUERY_LIMIT":
            raise GeocoderQuotaExceeded('Over query limit')
        elif status == "INTERNAL_SERVER_ERROR":  # not documented
            raise GeocoderUnavailable('Internal server error')
        else:
            # Unknown (undocumented) status.
            raise GeocoderServiceError('Unknown error')
