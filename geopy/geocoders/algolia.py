import collections.abc
from functools import partial
from urllib.parse import urlencode

from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.point import Point
from geopy.util import logger

__all__ = ('AlgoliaPlaces',)


class AlgoliaPlaces(Geocoder):
    """Geocoder using the Algolia Places API.

    Documentation at:
        https://community.algolia.com/places/documentation.html
    """

    geocode_path = '/1/places/query'
    reverse_path = '/1/places/reverse'

    def __init__(
            self,
            *,
            app_id=None,
            api_key=None,
            domain='places-dsn.algolia.net',
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """
        :param str app_id: Unique application identifier. It's used to
            identify you when using Algolia's API.
            See https://www.algolia.com/dashboard.

        :param str api_key: Algolia's user API key.

        :param str domain: Currently it is ``'places-dsn.algolia.net'``,
            can be changed for testing purposes.

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
        """
        super().__init__(
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
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
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            type=None,
            restrict_searchable_attributes=None,
            limit=None,
            language=None,
            countries=None,
            around=None,
            around_via_ip=None,
            around_radius=None,
            x_forwarded_for=None
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

        :param str type: Restrict the search results to a specific type.
            Available types are defined in documentation:
            https://community.algolia.com/places/api-clients.html#api-options-type

        :param str restrict_searchable_attributes: Restrict the fields in which
            the search is done.

        :param int limit: Limit the maximum number of items in the
            response. If not provided and there are multiple results
            Algolia API will return 20 results by default. This will be
            reset to one if ``exactly_one`` is True.

        :param str language: If specified, restrict the search results
            to a single language. You can pass two letters country
            codes (ISO 639-1).

        :param list countries: If specified, restrict the search results
            to a specific list of countries. You can pass two letters
            country codes (ISO 3166-1).

        :param around: Force to first search around a specific
            latitude longitude.
        :type around: :class:`geopy.point.Point`, list or tuple of
            ``(latitude, longitude)``, or string as ``"%(latitude)s,
            %(longitude)s"``.

        :param bool around_via_ip: Whether or not to first search
            around the geolocation of the user found via his IP address.
            This is true by default.

        :param int around_radius: Radius in meters to search around the
            latitude/longitude. Otherwise a default radius is
            automatically computed given the area density.

        :param str x_forwarded_for: Override the HTTP header X-Forwarded-For.
            With this you can control the source IP address used to resolve
            the geo-location of the user. This is particularly useful when
            you want to use the API from your backend as if it was from your
            end-users' locations.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """

        params = {
            'query': query,
        }

        if type is not None:
            params['type'] = type

        if restrict_searchable_attributes is not None:
            params['restrictSearchableAttributes'] = restrict_searchable_attributes

        if limit is not None:
            params['hitsPerPage'] = limit

        if exactly_one:
            params["hitsPerPage"] = 1

        if language is not None:
            params['language'] = language.lower()

        if countries is not None:
            params['countries'] = ','.join([c.lower() for c in countries])

        if around is not None:
            p = Point(around)
            params['aroundLatLng'] = "%s,%s" % (p.latitude, p.longitude)

        if around_via_ip is not None:
            params['aroundLatLngViaIP'] = \
                'true' if around_via_ip else 'false'

        if around_radius is not None:
            params['aroundRadius'] = around_radius

        url = '?'.join((self.geocode_api, urlencode(params)))
        headers = {}

        if x_forwarded_for is not None:
            headers['X-Forwarded-For'] = x_forwarded_for

        if self.app_id is not None and self.api_key is not None:
            headers['X-Algolia-Application-Id'] = self.app_id
            headers['X-Algolia-API-Key'] = self.api_key

        logger.debug('%s.geocode: %s', self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one, language=language)
        return self._call_geocoder(url, callback, headers=headers, timeout=timeout)

    def reverse(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            limit=None,
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

        :param int limit: Limit the maximum number of items in the
            response. If not provided and there are multiple results
            Algolia API will return 20 results by default. This will be
            reset to one if ``exactly_one`` is True.

        :param str language: If specified, restrict the search results
            to a single language. You can pass two letters country
            codes (ISO 639-1).

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        location = self._coerce_point_to_string(query)

        params = {
            'aroundLatLng': location,
        }

        if limit is not None:
            params['hitsPerPage'] = limit

        if language is not None:
            params['language'] = language

        url = '?'.join((self.reverse_api, urlencode(params)))
        headers = {}

        if self.app_id is not None and self.api_key is not None:
            headers['X-Algolia-Application-Id'] = self.app_id
            headers['X-Algolia-API-Key'] = self.api_key

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one, language=language)
        return self._call_geocoder(url, callback, headers=headers, timeout=timeout)

    def _parse_feature(self, feature, language):
        # Parse each resource.
        latitude = feature.get('_geoloc', {}).get('lat')
        longitude = feature.get('_geoloc', {}).get('lng')

        if isinstance(feature['locale_names'], collections.abc.Mapping):
            if language in feature['locale_names']:
                placename = feature['locale_names'][language][0]
            else:
                placename = feature['locale_names']["default"][0]
        else:
            placename = feature['locale_names'][0]

        return Location(placename, (latitude, longitude), feature)

    def _parse_json(self, response, exactly_one, language):
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
