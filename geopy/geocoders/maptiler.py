from geopy.compat import quote, string_compare, urlencode
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.point import Point
from geopy.util import logger

__all__ = ("MapTiler", )


class MapTiler(Geocoder):
    """Geocoder using the MapTiler API.

    Documentation at:
        https://cloud.maptiler.com/geocoding/ (requires sign-up)

    .. versionadded:: 1.22.0
    """

    api_path = '/geocoding/%(query)s.json'

    def __init__(
            self,
            api_key,
            format_string=None,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            domain='api.maptiler.com',
    ):
        """
        :param str api_key: The API key required by Maptiler to perform
            geocoding requests. API keys are managed through Maptiler's account
            page (https://cloud.maptiler.com/account/keys).

        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

            .. deprecated:: 1.22.0

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

        :param str domain: base api domain for Maptiler
        """
        super(MapTiler, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )
        self.api_key = api_key
        self.domain = domain.strip('/')
        self.api = "%s://%s%s" % (self.scheme, self.domain, self.api_path)

    def _parse_json(self, json, exactly_one=True):
        # Returns location, (latitude, longitude) from json feed.
        features = json['features']
        if not features:
            return None

        def parse_feature(feature):
            location = feature['place_name']
            longitude = feature['center'][0]
            latitude = feature['center'][1]

            return Location(location, (latitude, longitude), feature)
        if exactly_one:
            return parse_feature(features[0])
        else:
            return [parse_feature(feature) for feature in features]

    def geocode(
            self,
            query,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            proximity=None,
            language=None,
            bbox=None,
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

        :param proximity: A coordinate to bias local results based on a provided
            location.
        :type proximity: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param language: Prefer results in specific languages. Accepts
            a single string like ``"en"`` or a list like ``["de", "en"]``.
        :type language: str or list

        :param bbox: The bounding box of the viewport within which
            to bias geocode results more prominently.
            Example: ``[Point(22, 180), Point(-22, -180)]``.
        :type bbox: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = {'key': self.api_key}

        query = self.format_string % query
        if bbox:
            params['bbox'] = self._format_bounding_box(
                bbox, "%(lon1)s,%(lat1)s,%(lon2)s,%(lat2)s")

        if isinstance(language, string_compare):
            language = [language]
        if language:
            params['language'] = ','.join(language)

        if proximity:
            p = Point(proximity)
            params['proximity'] = "%s,%s" % (p.longitude, p.latitude)

        quoted_query = quote(query.encode('utf-8'))
        url = "?".join((self.api % dict(query=quoted_query),
                        urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    def reverse(
            self,
            query,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            language=None,
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

        :param language: Prefer results in specific languages. Accepts
            a single string like ``"en"`` or a list like ``["de", "en"]``.
        :type language: str or list

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = {'key': self.api_key}

        if isinstance(language, string_compare):
            language = [language]
        if language:
            params['language'] = ','.join(language)

        point = self._coerce_point_to_string(query, "%(lon)s,%(lat)s")
        quoted_query = quote(point.encode('utf-8'))
        url = "?".join((self.api % dict(query=quoted_query),
                        urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )
