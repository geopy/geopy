"""
Mapzen geocoder, contributed by Michal Migurski of Mapzen.
"""

from geopy.geocoders.base import (
    Geocoder,
    DEFAULT_FORMAT_STRING,
    DEFAULT_TIMEOUT,
    DEFAULT_SCHEME,
)
from geopy.compat import urlencode
from geopy.location import Location
from geopy.util import logger


__all__ = ("Mapzen", )


class Mapzen(Geocoder):
    """
    Mapzen Search geocoder. Documentation at:
        https://mapzen.com/documentation/search/

    .. warning::
       Please note that Mapzen has shut down their API so this geocoder
       class might be removed in future releases.
    """

    def __init__(
            self,
            api_key=None,
            format_string=DEFAULT_FORMAT_STRING,
            boundary_rect=None,
            country_bias=None,
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
            user_agent=None,
            domain='search.mapzen.com',
            scheme=DEFAULT_SCHEME,
    ):  # pylint: disable=R0913
        """
        :param str format_string: String containing '%s' where the
            string to geocode should be interpolated before querying the
            geocoder. For example: '%s, Mountain View, CA'. The default
            is just '%s'.

        :param tuple boundary_rect: Coordinates to restrict search within,
            given as (west, south, east, north) coordinate tuple.

        :param str country_bias: Bias results to this country (ISO alpha-3).

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

        :param str user_agent: Use a custom User-Agent header.

            .. versionadded:: 1.12.0

        :param str domain: Specify a custom domain for Mapzen API.

        :param str scheme: Use 'https' or 'http' as the API URL's scheme.
            Default is https. Note that SSL connections' certificates are not
            verified.

        """
        super(Mapzen, self).__init__(
            format_string, scheme, timeout, proxies, user_agent=user_agent
        )
        self.country_bias = country_bias
        self.format_string = format_string
        self.boundary_rect = boundary_rect
        self.api_key = api_key
        self.domain = domain.strip('/')

        self.geocode_api = '%s://%s/v1/search' % (self.scheme, self.domain)
        self.reverse_api = '%s://%s/v1/reverse' % (self.scheme, self.domain)

    def geocode(
            self,
            query,
            exactly_one=True,
            timeout=None,
    ):  # pylint: disable=R0913,W0221
        """
        Geocode a location query.

        :param str query: The address, query or structured query to geocode
            you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

            .. versionadded:: 0.97

        """
        params = {'text': self.format_string % query}

        if self.api_key:
            params.update({
                'api_key': self.api_key
            })

        if self.boundary_rect:
            params['boundary.rect.min_lon'] = self.boundary_rect[0]
            params['boundary.rect.min_lat'] = self.boundary_rect[1]
            params['boundary.rect.max_lon'] = self.boundary_rect[2]
            params['boundary.rect.max_lat'] = self.boundary_rect[3]

        if self.country_bias:
            params['boundary.country'] = self.country_bias

        url = "?".join((self.geocode_api, urlencode(params)))
        logger.debug("%s.geocode_api: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    def reverse(
            self,
            query,
            exactly_one=True,
            timeout=None,
    ):  # pylint: disable=W0221
        """
        Returns a reverse geocoded location.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

            .. versionadded:: 0.97

        """
        try:
            lat, lon = [
                x.strip() for x in
                self._coerce_point_to_string(query).split(',')
            ]  # doh
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")
        params = {
            'point.lat': lat,
            'point.lon': lon,
        }

        if self.api_key:
            params.update({
                'api_key': self.api_key
            })

        url = "?".join((self.reverse_api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    @staticmethod
    def parse_code(feature):
        """
        Parse each resource.
        """
        latitude = feature.get('geometry', {}).get('coordinates', [])[1]
        longitude = feature.get('geometry', {}).get('coordinates', [])[0]
        placename = feature.get('properties', {}).get('name')
        return Location(placename, (latitude, longitude), feature)

    def _parse_json(self, response, exactly_one):
        if response is None:
            return None
        features = response['features']
        if not len(features):
            return None
        if exactly_one:
            return self.parse_code(features[0])
        else:
            return [self.parse_code(feature) for feature in features]
