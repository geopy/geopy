import collections.abc
import warnings
from functools import partial
from urllib.parse import urlencode

from geopy.exc import (
    ConfigurationError,
    GeocoderAuthenticationFailure,
    GeocoderInsufficientPrivileges,
    GeocoderQuotaExceeded,
    GeocoderServiceError,
    GeocoderUnavailable,
)
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import join_filter, logger
from geopy.point import Point

__all__ = ("HereV7", )


class HereV7(Geocoder):
    """Geocoder using the HERE Geocoding & Search v7 API.
    
    Documentation at:
        https://developer.here.com/documentation/geocoding-search-api/
    
    ..attention::
        If you need to use the v6 API, use :class: `.HERE` instead.
    """

    structured_query_params = {
        'street',
        'houseNumber',
        'postalCode',
        'city',
        'district',
        'county',
        'state',
        'country'
    }

    geocode_path = '/v1/geocode'
    reverse_path = '/v1/revgeocode'

    def __init__(
            self,
            *,
            apikey=None,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """

        :param str apikey: Should be a valid HERE Maps apikey.
            More authentication details are available at
            https://developer.here.com/authenticationpage.

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
        """
        super().__init__(
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )

        domain = "search.hereapi.com"

        self.apikey = apikey
        self.api = "%s://geocode.%s%s" % (self.scheme, domain, self.geocode_path)
        self.reverse_api = (
            "%s://revgeocode.%s%s" % (self.scheme, domain, self.reverse_path)
        )

    def geocode(
        self,
        query,
        *,
        components=None,
        circle=None,
        country=None,
        bbox=None,
        language=None,
        exactly_one=True,
        maxresults=None,
        timeout=DEFAULT_SENTINEL
    ):
        """
        Return a location point by address.

        :param query: The address or query you wish to geocode.

            For a structured query, provide a dictionary whose keys are one of:
            `street`, `houseNumber`, `postalCode`, `city`, `district`
            `county`, `state`, `country`.

            You can specify a free-text query with conditional parameters
            by specifying a string in this param and a dict in the components
            parameter.
        
        :param dict components: Components to generate a qualified query.
        
            Provide a dictionary whose keys are one of: `street`, `houseNumber`,
            `postalCode`, `city`, `district`, `county`, `state`, `country`.
        
        :param circle: A type of spatial filter, limits the search for any other attributes
            in the request. Specified by one coordinate (lat/lon) and a radius (in meters).
        :type circle: list or tuple of 2 items: one :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"`` and a numeric
            value representing the radius of the circle.

            Only one of either circle, bbox or country can be provided.
        
        :param country: A list of country codes specified in `ISO 3166-1 alpha-3` format.
            This is a hard filter.

            Only one of either country, circle or bbox can be provided.

        :param bbox: A type of spatial filter, limits the search for any other attributes
            in the request. Specified by two coordinate (lat/lon)
            pairs -- corners of the box. `The bbox search is currently similar
            to mapview but it is not extended` (cited from the REST API docs).
            Relevant global results are also returned.
            Example: ``[Point(22, 180), Point(-22, -180)]``.
        :type bbox: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.

            Only one of either bbox, circle or country can be provided.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int maxresults: Defines the maximum number of items in the
            response structure. If not provided and there are multiple results
            the HERE API will return 10 results by default. This will be reset
            to one if ``exactly_one`` is True.

        :param str language: Affects the language of the response,
            must be a RFC 4647 language code, e.g. 'en-US'.


        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.
        """
        params = {}

        def create_structured_query(d):
            components = [
                "{}={}".format(key, val)
                for key, val
                in d.items() if key in self.structured_query_params
            ]
            if components: return ';'.join(components)
            else: return None

        if isinstance(query, dict):
            params['qq'] = create_structured_query(query)
        else:
            params['q'] = query
        
        if components and isinstance(components, dict):
            params['qq'] = create_structured_query(components)

        if circle:
            center, radius = circle
            center = Point(center)
            circle_str = "{latitude},{longitude};r={radius}".format(
                latitude=center.latitude,
                longitude=center.longitude,
                radius=radius
            )
            params['in'] = 'circle:' + circle_str
        
        if country:
            if isinstance(country, list):
                country_str = ','.join(country)
            else:
                country_str = country
            
            params['in'] = 'countryCode:' + country_str

        if bbox:
            bbox_str = self._format_bounding_box(
                bbox, "%(lon2)s,%(lat2)s,%(lon1)s,%(lat1)s"
            )
            params['in'] = 'bbox:' + bbox_str
        
        if maxresults:
            params['limit'] = maxresults

        if exactly_one:
            params['limit'] = 1

        if language:
            params['lang'] = language

        params['apiKey'] = self.apikey

        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(
            self,
            query,
            *,
            exactly_one=True,
            maxresults=None,
            language=None,
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

        :param int maxresults: Defines the maximum number of items in the
            response structure. If not provided and there are multiple results
            the HERE API will return 10 results by default. This will be reset
            to one if ``exactly_one`` is True.

        :param str language: Affects the language of the response,
            must be a RFC 4647 language code, e.g. 'en-US'.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        point = self._coerce_point_to_string(query, output_format="%(lat)s,%(lon)s")
        
        params = {
            'at': point,
            'apiKey': self.apikey
        }

        if maxresults:
            params['limit'] = min(maxresults, 100)
        if exactly_one:
            params['limit'] = 1
        if language:
            params['language'] = language

        url = "%s?%s" % (self.reverse_api, urlencode(params))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_json(self, doc, exactly_one=True):
        """
        Parse a location name, latitude, and longitude from an JSON response.
        """
        status_code = doc.get("statusCode", 200)
        if status_code != 200:
            err = doc.get('title') or doc.get('error_description')
            if status_code == 401:
                raise GeocoderAuthenticationFailure(err)
            elif status_code == 403:
                raise GeocoderInsufficientPrivileges(err)
            elif status_code == 429:
                raise GeocoderQuotaExceeded(err)
            elif status_code == 503:
                raise GeocoderUnavailable(err)
            else:
                raise GeocoderServiceError(err)

        try:
            resources = doc['items']
        except IndexError:
            resources = None

        if not resources:
            return None

        def parse_resource(resource):
            """
            Parse each return object.
            """
            stripchars = ", \n"

            location =resource['title']
            position = resource['position']

            latitude, longitude = position['lat'], position['lng']

            return Location(location, (latitude, longitude), resource)

        if exactly_one:
            return parse_resource(resources[0])
        else:
            return [parse_resource(resource) for resource in resources]
