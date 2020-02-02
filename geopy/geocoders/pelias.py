import warnings

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

    geocode_path = '/v1/search'
    reverse_path = '/v1/reverse'

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

        :type boundary_rect: list or tuple of 2 items of :class:`geopy.point.Point`
            or ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.
        :param boundary_rect: Coordinates to restrict search within.
            Example: ``[Point(22, 180), Point(-22, -180)]``.

            .. versionchanged:: 1.17.0
                Previously boundary_rect could be a list of 4 strings or numbers
                in the format of ``[longitude, latitude, longitude, latitude]``.
                This format is now deprecated in favor of a list/tuple
                of a pair of geopy Points and will be removed in geopy 2.0.

            .. deprecated:: 1.19.0
                This argument will be removed in geopy 2.0.
                Use `geocode`'s `boundary_rect` instead.

        :param str country_bias: Bias results to this country (ISO alpha-3).

            .. deprecated:: 1.19.0
                This argument will be removed in geopy 2.0.
                Use `geocode`'s `country_bias` instead.

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
        if country_bias is not None:
            warnings.warn(
                '`country_bias` argument of the %(cls)s.__init__ '
                'is deprecated and will be removed in geopy 2.0. Use '
                '%(cls)s.geocode(country_bias=%(value)r) instead.'
                % dict(cls=type(self).__name__, value=country_bias),
                DeprecationWarning,
                stacklevel=2
            )
        self.country_bias = country_bias
        if boundary_rect is not None:
            warnings.warn(
                '`boundary_rect` argument of the %(cls)s.__init__ '
                'is deprecated and will be removed in geopy 2.0. Use '
                '%(cls)s.geocode(boundary_rect=%(value)r) instead.'
                % dict(cls=type(self).__name__, value=boundary_rect),
                DeprecationWarning,
                stacklevel=2
            )
        self.boundary_rect = boundary_rect
        self.api_key = api_key
        self.domain = domain.strip('/')

        self.geocode_api = (
            '%s://%s%s' % (self.scheme, self.domain, self.geocode_path)
        )
        self.reverse_api = (
            '%s://%s%s' % (self.scheme, self.domain, self.reverse_path)
        )

    def geocode(
            self,
            query,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            boundary_rect=None,
            country_bias=None,
            language=None
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

        :type boundary_rect: list or tuple of 2 items of :class:`geopy.point.Point`
            or ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.
        :param boundary_rect: Coordinates to restrict search within.
            Example: ``[Point(22, 180), Point(-22, -180)]``.

            .. versionadded:: 1.19.0

        :param str country_bias: Bias results to this country (ISO alpha-3).

            .. versionadded:: 1.19.0

        :param str language: Preferred language in which to return results.
            Either uses standard
            `RFC2616 <http://www.ietf.org/rfc/rfc2616.txt>`_
            accept-language string or a simple comma-separated
            list of language codes.

            .. versionadded:: 1.21.0

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = {'text': self.format_string % query}

        if self.api_key:
            params.update({
                'api_key': self.api_key
            })

        if boundary_rect is None:
            boundary_rect = self.boundary_rect
        if boundary_rect:
            if len(boundary_rect) == 4:
                warnings.warn(
                    '%s `boundary_rect` format of '
                    '`[longitude, latitude, longitude, latitude]` is now '
                    'deprecated and will not be supported in geopy 2.0. '
                    'Use `[Point(latitude, longitude), Point(latitude, longitude)]` '
                    'instead.' % type(self).__name__,
                    DeprecationWarning,
                    stacklevel=2
                )
                lon1, lat1, lon2, lat2 = boundary_rect
                boundary_rect = [[lat1, lon1], [lat2, lon2]]
            lon1, lat1, lon2, lat2 = self._format_bounding_box(
                boundary_rect, "%(lon1)s,%(lat1)s,%(lon2)s,%(lat2)s").split(',')
            params['boundary.rect.min_lon'] = lon1
            params['boundary.rect.min_lat'] = lat1
            params['boundary.rect.max_lon'] = lon2
            params['boundary.rect.max_lat'] = lat2

        if country_bias is None:
            country_bias = self.country_bias
        if country_bias:
            params['boundary.country'] = country_bias

        if language:
            params["lang"] = language

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
            language=None
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

        :param str language: Preferred language in which to return results.
            Either uses standard
            `RFC2616 <http://www.ietf.org/rfc/rfc2616.txt>`_
            accept-language string or a simple comma-separated
            list of language codes.

            .. versionadded:: 1.21.0

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        try:
            lat, lon = self._coerce_point_to_string(query).split(',')
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")
        params = {
            'point.lat': lat,
            'point.lon': lon,
        }

        if language:
            params['lang'] = language

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
