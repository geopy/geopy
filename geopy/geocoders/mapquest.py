from geopy.compat import quote, string_compare, urlencode
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.point import Point
from geopy.util import logger

__all__ = ("MapQuest", )


class MapQuest(Geocoder):
    """Geocoder using the MapQuest API
    Documentation at:
        https://developer.mapquest.com/documentation/geocoding-api/
    """
    geocode_path = '/geocoding/v1/address'
    reverse_path = '/geocoding/v1/reverse'

    def __init__(
        self,
        api_key,
        format_string=None,
        scheme=None,
        timeout=DEFAULT_SENTINEL,
        proxies=DEFAULT_SENTINEL,
        user_agent=None,
        ssl_context=DEFAULT_SENTINEL,
        domain='www.mapquestapi.com',
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
        super(MapQuest, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )

        self.api_key = api_key
        self.domain = domain.strip('/')
        self.api = "%s://%s" % (self.scheme, self.domain)

    def _parse_json(self, json, exactly_one=True):
        '''Returns location, (latitude, longitude) from json feed.'''
        features = json['results'][0]['locations']

        if features == []:
            return None
        
        def parse_location(feature):
            addr_keys = [
                'street',
                'adminArea6',
                'adminArea5',
                'adminArea4',
                'adminArea3',
                'adminArea2',
                'adminArea1',
                'postalCode'
            ]

            location = []

            for k in addr_keys:
                if k in feature and feature[k]:
                    location.append(feature[k])
            return ", ".join(location)

        def parse_feature(feature):
            location = parse_location(feature)
            longitude = feature['latLng']['lng']
            latitude = feature['latLng']['lat']
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
        country=None,
        bbox=None
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

        :param bbox: The bounding box of the viewport within which
            to bias geocode results more prominently.
            Example: ``[Point(22, 180), Point(-22, -180)]``.
        :type bbox: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = {}
        params['key'] = self.api_key
        params['location'] = query
        
        if bbox:
            params['boundingBox'] = self._format_bounding_box(
                bbox, "%(lon1)s,%(lat1)s,%(lon),%(lat2)s"
            )
        
        url = self.api + self.geocode_path + "?" + urlencode(params)

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)

        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )
    
    def reverse(
        self,
        query,
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
        params['key'] = self.api_key

        point = self._coerce_point_to_string(query, "%(lat)s,%(lon)s")
        params['location'] = point
        
        url = self.api + self.reverse_path + "?" + urlencode(params)

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)

        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )