from functools import partial
from urllib.parse import quote, urlencode

from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.point import Point
from geopy.util import logger

__all__ = ("MapBox", )


class MapBox(Geocoder):
    """Geocoder using the Mapbox API.

    Documentation at:
        https://www.mapbox.com/api-documentation/
    """

    api_path = '/geocoding/v5/mapbox.places/%(query)s.json/'

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
            domain='api.mapbox.com',
            referer=None
    ):
        """
        :param str api_key: The API key required by Mapbox to perform
            geocoding requests. API keys are managed through Mapox's account
            page (https://www.mapbox.com/account/access-tokens).

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

            .. versionadded:: 2.0

        :param str domain: base api domain for mapbox

        :param str referer: The URL used to satisfy the URL restriction of
            mapbox tokens.

            .. versionadded:: 2.3
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
        self.api = "%s://%s%s" % (self.scheme, self.domain, self.api_path)
        if referer:
            self.headers['Referer'] = referer

    def _parse_json(self, json, exactly_one=True):
        '''Returns location, (latitude, longitude) from json feed.'''
        features = json['features']
        if features == []:
            return None

        def parse_feature(feature):
            location = feature['place_name']
            longitude = feature['geometry']['coordinates'][0]
            latitude = feature['geometry']['coordinates'][1]
            return Location(location, (latitude, longitude), feature)
        if exactly_one:
            return parse_feature(features[0])
        else:
            return [parse_feature(feature) for feature in features]

    def geocode(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            proximity=None,
            country=None,
            language=None,
            bbox=None
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

        :param country: Country to filter result in form of
            ISO 3166-1 alpha-2 country code (e.g. ``FR``).
            Might be a Python list of strings.

        :type country: str or list

        :param str language: This parameter controls the language of the text supplied in
            responses, and also affects result scoring, with results matching the user’s
            query in the requested language being preferred over results that match in
            another language. You can pass two letters country codes (ISO 639-1).

            .. versionadded:: 2.3

        :param bbox: The bounding box of the viewport within which
            to bias geocode results more prominently.
            Example: ``[Point(22, 180), Point(-22, -180)]``.
        :type bbox: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = {}

        params['access_token'] = self.api_key
        if bbox:
            params['bbox'] = self._format_bounding_box(
                bbox, "%(lon1)s,%(lat1)s,%(lon2)s,%(lat2)s")

        if not country:
            country = []
        if isinstance(country, str):
            country = [country]
        if country:
            params['country'] = ",".join(country)

        if proximity:
            p = Point(proximity)
            params['proximity'] = "%s,%s" % (p.longitude, p.latitude)

        if language:
            params['language'] = language

        quoted_query = quote(query.encode('utf-8'))
        url = "?".join((self.api % dict(query=quoted_query),
                        urlencode(params)))
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
        params = {}
        params['access_token'] = self.api_key

        point = self._coerce_point_to_string(query, "%(lon)s,%(lat)s")
        quoted_query = quote(point.encode('utf-8'))
        url = "?".join((self.api % dict(query=quoted_query),
                        urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)
