from functools import partial
from urllib.parse import urlencode

from geopy.geocoders.base import Geocoder, DEFAULT_SENTINEL

from geopy.util import logger

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
        """
        params = '?text={}'.format(query)
        url = self.api_geocode + params

        logger.debug('%s.geocode: %s', self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout, headers=self.headers)

    def _parse_json(self, response, exactly_one):
        if response is None or 'features' not in response:
            return None

        features = response['features']

        if exactly_one:
            return self._parse_feature(features[0])

        return [self._parse_feature(i) for i in features]

    def _parse_feature(self, feature):
        latitude, longitude = self._get_coordinates(feature)
        place_name = self._get_place_name(feature)

    def _get_place_name(self, feature):
        return feature.get('properties', {}).get('label')

    def _get_coordinates(self, feature):
        coordinates = feature.get('geometry', {}).get('coordinates', [])
        latitude = None
        longitude = None

        if len(coordinates) == 2:
            latitude = coordinates[0]
            longitude = coordinates[1]

        return latitude, longitude
