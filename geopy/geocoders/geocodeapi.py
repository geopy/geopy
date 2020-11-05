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

    _param_templates = {
        'size': '&size={}',
        'country': '&boundary.country={}',
        'circle_lat': '&boundary.circle.lat={}',
        'circle_lon': '&boundary.circle.lon={}',
        'circle_radius': '&boundary.circle.radius={}',
        'rect_min_lat': '&boundary.rect.min_lat={}',
        'rect_min_lon': '&boundary.rect.min_lon={}',
        'rect_max_lat': '&boundary.rect.max_lat={}',
        'rect_max_lon': '&boundary.rect.max_lon={}',
        'point_lat': '&focus.point.lat={}',
        'point_lon': '&focus.point.lon={}',
        'reverse_point_lat': '&point.lat={}',
        'reverse_point_lon': '&point.lon={}',
        'layers': '&layers={}',
    }

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
        rect_min_lat=None,
        rect_min_lon=None,
        rect_max_lat=None,
        rect_max_lon=None,
        point_lat=None,
        point_lon=None,
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

        :param float rect_min_lat: Minimum latitude for limit search to rectangle

        :param float rect_min_lon: Minimum longitude for limit search to rectangle

        :param float rect_max_lat: Maximum latitude for limit search to rectangle

        :param float rect_max_lon: Maximum longitude for limit search to rectangle

        :param float point_lat: Latitude for prioritize around a point

        :param float point_lon: Longitude for prioritize around a point
        """
        params = self._get_params(
            query,
            size=size,
            country=country,
            circle_lat=circle_lat,
            circle_lon=circle_lon,
            circle_radius=circle_radius,
            rect_min_lat=rect_min_lat,
            rect_min_lon=rect_min_lon,
            rect_max_lat=rect_max_lat,
            rect_max_lon=rect_max_lon,
            point_lon=point_lon,
            point_lat=point_lat,
        )

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

    def _get_params(self, query, **kwargs):
        params = '?text={}'.format(query)

        additional_params = []
        for k, v in kwargs.items():
            if v is not None:
                try:
                    additional_params.append(self._param_templates[k].format(v))
                except KeyError:
                    raise KeyError('Wrong parameter: %s' % k)
        if not additional_params:
            return params

        return params + ''.join(additional_params)

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
