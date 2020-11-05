from functools import partial
from urllib.parse import urlencode

from geopy.geocoders.base import Geocoder, DEFAULT_SENTINEL
from geopy.util import logger
from geopy.location import Location

from geopy.exc import (
    GeocoderAuthenticationFailure,
    GeocoderNotFound,
    GeocoderServiceError,
)

__all__ = ('GeocodeAPI',)


class GeocodeAPI(Geocoder):
    """Geocoder using the Geocode API.

    Documentation at:
        https://geocodeapi.io/documentation/

    """
    base_api_url = 'https://app.geocodeapi.io/api/v1/'
    geocode_path = 'search'
    reverse_path = 'reverse'

    def __init__(
        self,
        api_key,
        *,
        timeout=DEFAULT_SENTINEL,
        proxies=DEFAULT_SENTINEL,
    ):
        """
        :param str api_key: The API key required by GeocodeFarm
            to perform geocoding requests.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.
        """
        super().__init__(timeout=timeout, proxies=proxies)

        self.headers = {'apikey': api_key}

        self.api_geocode = self.base_api_url + self.geocode_path
        self.api_reverse = self.base_api_url + self.reverse_path

    def geocode(
        self,
        query,
        *,
        exactly_one=True,
        timeout=DEFAULT_SENTINEL,
        size=None,
        country=None,
        circle_lat=None,
        circle_lon=None,
        circle_radius=None,
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

        :param int size: Limits the number of results to be returned

        :param str country: Limits the search to a list of specified countries.
            Comma separated list of alpha-2 or alpha-3 ISO-3166 country code.

        :param float circle_lat: Latitude for limit search to radius

        :param float circle_lon: Longitude for limit search to radius

        :param int circle_radius: Radius around the coordinates circle_lat and circle_lon
        """
        params = '?text={}'.format(query)

        if size is not None:
            params += '&size={}'.format(size)

        if country is not None:
            params += '&boundary.country={}'.format(country)

        if circle_lat is not None:
            params += '&boundary.circle.lat{}'.format(circle_lat)

        if circle_lon is not None:
            params += '&boundary.circle.lon{}'.format(circle_lon)

        if circle_radius is not None:
            params += '&boundary.circle.radius={}'.format(circle_radius)

        url = self.api_geocode + params

        logger.debug('%s.geocode: %s', self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout, headers=self.headers)

    def reverse(
        self,
        query,
        *,
        exactly_one=True,
        timeout=DEFAULT_SENTINEL,
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
        """
        location = self._coerce_point_to_string(
            query, output_format='point.lat=%(lat)s&point.lon=%(lon)s'
        )
        url = '{}?{}'.format(self.api_reverse, location)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout, headers=self.headers)

    def _parse_json(self, response, exactly_one):
        if response is None or 'features' not in response:
            return None

        features = response['features']
        if len(features) == 0:
            return None

        if exactly_one:
            return self._parse_feature(features[0])

        return [self._parse_feature(i) for i in features]

    def _parse_feature(self, feature):
        latitude, longitude = self._get_coordinates(feature)
        place_name = self._get_place_name(feature)

        return Location(place_name, (latitude, longitude), feature)

    def _get_place_name(self, feature):
        return feature.get('properties', {}).get('label')

    def _get_coordinates(self, feature):
        coordinates = feature.get('geometry', {}).get('coordinates', [])
        latitude = None
        longitude = None

        if len(coordinates) == 2:
            latitude = coordinates[1]
            longitude = coordinates[0]

        return latitude, longitude
