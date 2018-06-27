from geopy.compat import urlencode
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("Pelias", )


class Pelias(Geocoder):
    """Pelias geocoder.

    Documentation at:
        https://github.com/pelias/documentation

    See also :class:`geopy.geocoders.GeocodeEarth` which is a Pelias-based
    service provided by the developers of Pelias itself.

    .. versionchanged:: 1.15.0
       ``Mapzen`` geocoder has been renamed to ``Pelias``.

    """

    def __init__(
            self,
            domain,
            api_key=None,
            format_string=None,
            boundary_rect=None,
            country_bias=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            scheme=None,
            ssl_context=DEFAULT_SENTINEL,
            # Make sure to synchronize the changes of this signature in the
            # inheriting classes (e.g. GeocodeEarth).
    ):
        """
        :param str domain: Specify a domain for Pelias API.

        :param str api_key: Pelias API key, optional.

        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

        :param tuple boundary_rect: Coordinates to restrict search within,
            given as (west, south, east, north) coordinate tuple.

        :param str country_bias: Bias results to this country (ISO alpha-3).

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str user_agent:
            See :attr:`geopy.geocoders.options.default_user_agent`.

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`.

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.

        """
        super(Pelias, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )
        self.country_bias = country_bias
        self.boundary_rect = boundary_rect
        self.api_key = api_key
        self.domain = domain.strip('/')

        self.geocode_api = '%s://%s/v1/search' % (self.scheme, self.domain)
        self.reverse_api = '%s://%s/v1/reverse' % (self.scheme, self.domain)

    def geocode(
            self,
            query,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
    ):
        """
        Return a location point by address.

        :param str query: The address, query or structured query to geocode
            you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
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

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
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
        # TODO make this a private API
        # Parse each resource.
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
