from geopy.compat import urlencode, quote
from geopy.exc import (
    GeocoderQueryError,
)
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("MapBox", )


class MapBox(Geocoder):
    """Geocoder using the Mapbox API.

    Documentation at:
        https://www.mapbox.com/api-documentation/

    .. versionadded:: 1.17.0
    """

    api_path = '/geocoding/v5/mapbox.places/%(query)s.json/'

    def __init__(
            self,
            api_key,
            format_string=None,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            domain='api.mapbox.com',
    ):
        """
        :param str api_key: The API key required by Mapbox to perform
            geocoding requests. API keys are managed through Mapox's account
            page (https://www.mapbox.com/account/access-tokens).

        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

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

        :param str domain: base api domain for mapbox
        """
        super(MapBox, self).__init__(
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

    @staticmethod
    def _format_bbox_param(bbox):
        """
        Format the bbox to something Mapbox understands.
        """
        return '%f,%f,%f,%f' % (bbox[0], bbox[1], bbox[2], bbox[3])

    @staticmethod
    def _format_proximity_param(proximity):
        """
        Format the proximity to something Mapbox understands.
        """
        return '%f,%f' % (proximity[0], proximity[1])

    def _parse_json(self, json, exactly_one=True):
        '''Returns location, (latitude, longitude) from json feed.'''
        features = json['features']
        if features == []:
            return None

        def parse_feature(feature):
            location = feature['place_name']
            place = feature['text']
            longitude = feature['geometry']['coordinates'][0]
            latitude = feature['geometry']['coordinates'][1]
            return Location(location, (latitude, longitude), place)
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
            country=None,
            bbox=None,
    ):
        """
        Return a location point by address

        :param str query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param proximity: a coordinate to bias local results based on a provided location.
        :type proximity: list of tuple

        :param string country: Country to filter result in form of
            ISO 3166-1 alpha-2 country code.

        :param bbox: The bounding box of the viewport within which
            to bias geocode results more prominently.
        :type bbox: list or tuple

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = {}

        params['access_token'] = self.api_key
        query = self.format_string % query
        if bbox:
            if len(bbox) != 4:
                raise GeocoderQueryError(
                    "bbox must be a four-item iterable of lat,lon,lat,lon"
                )
            params['bbox'] = self._format_bbox_param(bbox)

        if country:
            params['country'] = country

        if proximity:
            if len(proximity) != 2:
                raise GeocoderQueryError(
                    "proximity must be a two-item iterable of lat,lon"
                )
            params['proximity'] = self._format_proximity_param(proximity)

        quoted_query = quote(query.encode('utf-8'))
        url = "?".join((self.api % dict(query=quoted_query),
                        urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)

        return self._parse_json(
            self._call_geocoder(url, timeout=timeout)
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
        params = {}
        params['access_token'] = self.api_key

        point = self._coerce_point_to_string(query, "%(lon)s,%(lat)s")
        quoted_query = quote(point.encode('utf-8'))
        url = "?".join((self.api % dict(query=quoted_query),
                        urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)

        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )
