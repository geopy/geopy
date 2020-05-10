from geopy.compat import (
    Request,
    urlencode,
)
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ('AlgoliaPlaces',)


class AlgoliaPlaces(Geocoder):
    """Geocoder using the Algolia Places API.

    Documentation at:
        https://community.algolia.com/places/documentation.html

    .. versionadded:: 1.22.0
    """

    geocode_path = '/1/places/query'
    reverse_path = '/1/places/reverse'

    def __init__(
            self,
            app_id=None,
            api_key=None,
            domain='places-dsn.algolia.net',
            format_string=None,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """
        :param str app_id: Unique application identifier. It's used to
            identify you when using Algolia's API.

        :param str api_key: Algolia's user API key.

        :param str domain: Currently it is ``'places-dsn.algolia.net'``,
            can be changed for testing purposes.

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

        """
        super(AlgoliaPlaces, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )
        self.domain = domain.strip('/')

        self.app_id = app_id
        self.api_key = api_key

        self.geocode_api = (
            '%s://%s%s' % (self.scheme, self.domain, self.geocode_path)
        )
        self.reverse_api = (
            '%s://%s%s' % (self.scheme, self.domain, self.reverse_path)
        )

    def geocode(
            self,
            query,
            type=None,
            restrict_searchable_attributes=None,
            limit=None,
            exactly_one=True,
            language=None,
            countries=None,
            around_lat_lng=None,
            around_lat_lng_via_ip=None,
            around_radius=None,
            x_forwarded_for=None,
            timeout=DEFAULT_SENTINEL,
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

        :param str type: Restrict the search results to a specific type.
            Available types are defined in documentation:
            https://community.algolia.com/places/api-clients.html#api-options-type

        :param str restrict_searchable_attributes: Restrict the fields in which
            the search is done.

        :param int limit: Limit the maximum number of items in the
            response. If not provided and there are multiple results
            Algolia API will return 20 results by default. This will be
            reset to one if ``exactly_one`` is True.

        :param bool exactly_one: Restrict the response to one resource.

        :param str language: If specified, restrict the search results
            to a single language. You can pass two letters country
            codes (ISO 639-1).

        :param list countries: If specified, restrict the search results
            to a specific list of countries. You can pass two letters
            country codes (ISO 3166-1).

        :param str around_lat_lng: Force to first search around a specific
            latitude longitude. The option value must be provided as a
            string: `latitude,longitude` like `12.232,23.1`.

        :param bool around_lat_lng_via_ip: Whether or not to first search
            around the geolocation of the user found via his IP address.
            This is true by default.

        :param around_radius: Radius in meters to search around the
            latitude/longitude. Otherwise a default radius is
            automatically computed given the area density.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param str x_forwarded_for: Override the HTTP header X-Forwarded-For.
            With this you can control the source IP address used to resolve
            the geo-location of the user. This is particularly useful when
            you want to use the API from your backend as if it was from your
            end-users locations.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """

        params = {
            'query': self.format_string % query,
        }

        _parse_json_kwargs = {}

        if type is not None:
            params['type'] = type

        if restrict_searchable_attributes is not None:
            params['restrictSearchableAttributes'] = \
                restrict_searchable_attributes

        if limit is not None:
            params['hitsPerPage'] = limit

        if exactly_one:
            params["hitsPerPage"] = 1

        if language is not None:
            params['language'] = language.lower()
            _parse_json_kwargs['language'] = language

        if countries is not None:
            params['countries'] = ','.join([c.lower() for c in countries])

        if around_lat_lng is not None:
            params['aroundLatLng'] = around_lat_lng

        if isinstance(around_lat_lng_via_ip, bool):
            params['aroundLatLngViaIP'] = \
                'true' if around_lat_lng_via_ip else 'false'

        if around_radius is not None:
            params['aroundRadius'] = around_radius

        url = '?'.join((self.geocode_api, urlencode(params)))
        request = Request(url)

        if x_forwarded_for is not None:
            request.add_header('X-Forwarded-For', x_forwarded_for)

        if self.app_id is not None and self.api_key is not None:
            request.add_header('X-Algolia-Application-Id', self.app_id)
            request.add_header('X-Algolia-API-Key', self.api_key)

        logger.debug('%s.geocode: %s', self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(request, timeout=timeout),
            exactly_one,
            **_parse_json_kwargs,
        )

    def reverse(
            self,
            query,
            exactly_one=True,
            limit=None,
            language=None,
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

        :param int limit: Limit the maximum number of items in the
            response. If not provided and there are multiple results
            Algolia API will return 20 results by default. This will be
            reset to one if ``exactly_one`` is True.

        :param str language: If specified, restrict the search results
            to a single language. You can pass two letters country
            codes (ISO 639-1).

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        try:
            lat, lng = self._coerce_point_to_string(query).split(',')
        except ValueError:
            raise ValueError('Must be a coordinate pair or Point')

        params = {
            'aroundLatLng': '%s,%s' % (lat, lng),
        }

        _parse_json_kwargs = {}

        if limit is not None:
            params['hitsPerPage'] = limit

        if language is not None:
            params['language'] = language
            _parse_json_kwargs['language'] = language

        url = '?'.join((self.reverse_api, urlencode(params)))
        request = Request(url)

        if self.app_id is not None and self.api_key is not None:
            request.add_header('X-Algolia-Application-Id', self.app_id)
            request.add_header('X-Algolia-API-Key', self.api_key)

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(request, timeout=timeout),
            exactly_one,
            **_parse_json_kwargs,
        )

    @staticmethod
    def _parse_feature(feature, language="default"):
        # Parse each resource.
        latitude = feature.get('_geoloc', {}).get('lat')
        longitude = feature.get('_geoloc', {}).get('lng')
        placename = feature['locale_names'].get(language)[0] \
            if isinstance(feature['locale_names'], dict) \
            else feature['locale_names'][0]
        return Location(placename, (latitude, longitude), feature)

    @classmethod
    def _parse_json(self, response, exactly_one, language='default'):
        if response is None or 'hits' not in response:
            return None
        features = response['hits']
        if not len(features):
            return None
        if exactly_one:
            return self._parse_feature(features[0], language=language)
        else:
            return [
                self._parse_feature(feature, language=language) for feature in features
            ]
