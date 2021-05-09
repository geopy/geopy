import collections.abc

from functools import partial
from urllib.parse import urlencode

from geopy.geocoders.base import Geocoder, DEFAULT_SENTINEL
from geopy.util import logger
from geopy.location import Location

__all__ = ("GeocodeAPI",)


class GeocodeAPI(Geocoder):
    """Geocoder using the Geocode API.

    Documentation at:
        https://geocodeapi.io/documentation/

    """

    base_api_url = "https://app.geocodeapi.io/api/v1/"
    geocode_path = "search"
    reverse_path = "reverse"

    structured_query_params = {
        "size",
        "boundary.country",
        "boundary.circle.lat",
        "boundary.circle.lon",
        "boundary.circle.radius",
        "boundary.rect.min_lat",
        "boundary.rect.min_lon",
        "boundary.rect.max_lat",
        "boundary.rect.max_lon",
        "layers",
    }

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
    ):
        """
        :param str api_key: The API key required by GeocodeAPI
            to perform geocoding requests.

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
        super().__init__(
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
            scheme=scheme,
        )

        self.api_key = api_key

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
        point=None,
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

        :type point: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.

        :param point: Prefer this area to find search results. By default this is
            treated as a hint, if you want to restrict results to this area,
            specify ``bounded=True`` as well.
            Example: ``[Point(22, 180), Point(-22, -180)]``.
        """

        if isinstance(query, collections.abc.Mapping):
            params = {
                key: val
                for key, val in query.items()
                if key in self.structured_query_params
            }
        else:
            params = {"text": query}
        if size:
            params["size"] = size
        if country:
            params["boundary.country"] = country
        if circle_lat:
            params["boundary.circle.lat"] = circle_lat
        if circle_lon:
            params["boundary.circle.lon"] = circle_lon
        if circle_radius:
            params["boundary.circle.radius"] = circle_radius
        if rect_min_lat:
            params["boundary.rect.min_lat"] = rect_min_lat
        if rect_min_lon:
            params["boundary.rect.min_lon"] = rect_min_lon
        if rect_max_lat:
            params["boundary.rect.max_lat"] = rect_max_lat
        if rect_max_lon:
            params["boundary.rect.max_lon"] = rect_max_lon
        if point:
            params["focus.point.lon"] = point.longitude
            params["focus.point.lat"] = point.latitude

        url = "?".join((self.api_geocode, urlencode(params)))
        headers = {"apikey": self.api_key}

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout, headers=headers)

    def reverse(
        self,
        query,
        *,
        exactly_one=True,
        timeout=DEFAULT_SENTINEL,
        size=None,
        layers=None,
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

        :param int size: Limits the number of results to be returned

        :param str layers: Filter search to a particular location type, e.g. venue,
            address, street, country, region, locality

        """
        headers = {"apikey": self.api_key}
        params = {
            "point.lat": query.latitude,
            "point.lon": query.longitude,
        }
        if size:
            params["size"] = size
        if layers:
            params["layers"] = layers
        url = "?".join((self.api_reverse, urlencode(params)))
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout, headers=headers)

    def _parse_json(self, response, exactly_one):
        if response is None or "features" not in response:
            return None

        features = response["features"]
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
        return feature.get("properties", {}).get("label")

    def _get_coordinates(self, feature):
        coordinates = feature.get("geometry", {}).get("coordinates", [])
        latitude = None
        longitude = None

        if len(coordinates) == 2:
            latitude = coordinates[1]
            longitude = coordinates[0]

        return latitude, longitude
