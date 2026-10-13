import collections.abc
import datetime
import json
from calendar import timegm
from functools import partial
from urllib.parse import urlencode

from geopy.adapters import AdapterHTTPError, get_retry_after
from geopy.exc import GeocoderQueryError, GeocoderRateLimited, GeocoderServiceError
from geopy.geocoders.base import DEFAULT_SENTINEL, ERROR_CODE_MAP, Geocoder
from geopy.location import Location
from geopy.timezone import ensure_pytz_is_installed, from_timezone_name
from geopy.util import logger

__all__ = ("MyGeocode", )


class MyGeocode(Geocoder):
    """Geocoder using the My Geocode API.

    An API key is optional: requests without a key are answered within
    a free daily allowance per network.

    Documentation at:
        https://www.mygeocode.com/docs/

    Pricing details:
        https://www.mygeocode.com/pricing/

    Terms of Service at:
        https://www.mygeocode.com/terms/

    .. versionadded:: 2.6
    """

    structured_query_params = {
        'street',
        'city',
        'state',
        'postcode',
        'country',
    }

    geocode_path = '/v1/forward'
    reverse_path = '/v1/reverse'
    autocomplete_path = '/v1/autocomplete'
    timezone_path = '/v1/timezone'

    def __init__(
            self,
            api_key=None,
            *,
            domain='api.mygeocode.com',
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """

        :param str api_key: My Geocode API key, optional. Without a key
            the requests are counted against the free daily allowance
            of your network. Keys are created after signing up at
            https://www.mygeocode.com/signup.

        :param str domain: Currently it is ``'api.mygeocode.com'``, can
            be changed for testing purposes.

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

        self.api_key = api_key
        self.domain = domain.strip('/')
        self.geocode_api = (
            '%s://%s%s' % (self.scheme, self.domain, self.geocode_path)
        )
        self.reverse_api = (
            '%s://%s%s' % (self.scheme, self.domain, self.reverse_path)
        )
        self.autocomplete_api = (
            '%s://%s%s' % (self.scheme, self.domain, self.autocomplete_path)
        )
        self.timezone_api = (
            '%s://%s%s' % (self.scheme, self.domain, self.timezone_path)
        )

    def geocode(
            self,
            query=None,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            limit=None,
            countries=None,
            bounds=None,
            bounded=False,
            proximity=None,
            types=None,
            language=None,
            place_id=None,
            typeahead=False,
            annotations=False
    ):
        """
        Return a location point by address.

        :param query: The address, query or a structured query
            you wish to geocode. Can be omitted when ``place_id`` is given.

            For a structured query, provide a dictionary whose keys
            are one of: `street`, `city`, `state`, `postcode` or `country`
            (a 2 character ISO 3166-1 alpha-2 code).
        :type query: dict or str

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param int limit: The maximum number of matches to return
            (the service accepts 1 to 10, default 5). This will be reset
            to 1 if ``exactly_one`` is ``True``.

        :param countries: Restricts the results to the specified
            country or countries. The country code is a 2 character code as
            defined by the ISO 3166-1 Alpha 2 standard (e.g. ``fr``).
            Might be a Python list of strings.
        :type countries: str or list

        :type bounds: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.
        :param bounds: The bounding box of the viewport within which
            to bias geocode results more prominently.
            Example: ``[Point(22, 180), Point(-22, -180)]``.

        :param bool bounded: Restrict the results to only items contained
            within the bounding ``bounds``.

        :param proximity: A coordinate to bias results towards.
        :type proximity: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param types: Restricts the results to the specified feature types.
            Allowed values: `address`, `street`, `postcode`, `city`, `region`,
            `country`, `poi`. Might be a Python list of strings.
        :type types: str or list

        :param str language: The language in which to return results,
            as an ISO 639-1 code (e.g. ``de``). The service uses ``en``
            when it is omitted.

        :param str place_id: Retrieve a Location using a place id from
            :attr:`.Location.raw` of an earlier result.
            Cannot be used with ``query`` or ``typeahead``.

        :param bool typeahead: If set, the query is interpreted as a partial
            input (as typed into a search box) and the service returns
            suggestions. Suggestions have an address and coordinates, but
            no address components in :attr:`.Location.raw`.
            Cannot be used with a structured query.

        :param bool annotations: Enable extra data (timezone, elevation,
            location codes, country information and more, see
            https://www.mygeocode.com/docs/forward-geocoding/#annotations),
            which can be accessed via :attr:`.Location.raw`.
            Not available with ``typeahead``.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        if place_id and query:
            raise ValueError(
                'Only one of the `query` or `place_id` parameters must be entered.')
        if place_id and typeahead:
            raise ValueError('`place_id` cannot be used with `typeahead`.')
        if query is None and place_id is None:
            raise ValueError('Either `query` or `place_id` must be set.')

        if place_id:
            params = {'place_id': place_id}
        elif isinstance(query, collections.abc.Mapping):
            if typeahead:
                raise ValueError('`typeahead` cannot be used with a structured query.')
            params = {
                key: val
                for key, val
                in query.items()
                if key in self.structured_query_params
            }
        else:
            params = {'q': query}

        if exactly_one:
            limit = 1
        if limit is not None:
            params['limit'] = limit

        if isinstance(countries, str):
            countries = [countries]
        if countries:
            params['countries'] = ",".join(countries)

        if bounds:
            params['bounds'] = self._format_bounding_box(
                bounds, "%(lat1)s,%(lon1)s,%(lat2)s,%(lon2)s")
            if bounded:
                params['strict'] = 1

        if proximity:
            params['proximity'] = self._coerce_point_to_string(proximity)

        if isinstance(types, str):
            types = [types]
        if types:
            params['types'] = ",".join(types)

        if language:
            params['lang'] = language

        if annotations and not typeahead:
            params['annotations'] = 1

        if self.api_key:
            params['key'] = self.api_key

        if typeahead:
            api = self.autocomplete_api
            callback = partial(self._parse_suggestions, exactly_one=exactly_one)
        else:
            api = self.geocode_api
            callback = partial(self._parse_json, exactly_one=exactly_one)
        url = "?".join((api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            language=None,
            level=None,
            radius=None,
            annotations=False
    ):
        """
        Return an address by location point.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable address.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param bool exactly_one: Return one result or a list of results, if
            available. The service returns at most one result, so the list
            contains a single item.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param str language: The language in which to return results,
            as an ISO 639-1 code (e.g. ``de``). The service uses ``en``
            when it is omitted.

        :param str level: The most detailed level to return. Allowed values:
            `address` (the default), `street`, `postcode`, `city`, `region`,
            `country`.

        :param int radius: Search radius in meters for addresses and streets,
            1 to 5000 (the service default is 5000). Nothing is returned
            if no address is that close.

        :param bool annotations: Enable extra data (timezone, elevation,
            location codes, country information and more, see
            https://www.mygeocode.com/docs/forward-geocoding/#annotations),
            which can be accessed via :attr:`.Location.raw`.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        try:
            lat, lon = self._coerce_point_to_string(query).split(',')
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")
        params = {
            'lat': lat,
            'lon': lon,
        }

        if language:
            params['lang'] = language
        if level:
            params['level'] = level
        if radius is not None:
            params['radius'] = int(radius)
        if annotations:
            params['annotations'] = 1
        if self.api_key:
            params['key'] = self.api_key

        url = "?".join((self.reverse_api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_reverse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse_timezone(self, query, *, at_time=None, timeout=DEFAULT_SENTINEL):
        """
        Find the timezone a point in `query` was in for a specified `at_time`.

        The service always returns a timezone: points at sea get
        a nautical ``Etc/GMT`` zone.

        :param query: The coordinates for which you want a timezone.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param at_time: The time at which you want the timezone of this
            location. This is optional, and defaults to the time that the
            function is called in UTC. Timezone-aware datetimes are correctly
            handled and naive datetimes are silently treated as UTC.
        :type at_time: :class:`datetime.datetime` or None

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: :class:`geopy.timezone.Timezone`.
        """
        ensure_pytz_is_installed()

        try:
            lat, lon = self._coerce_point_to_string(query).split(',')
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")
        params = {
            'lat': lat,
            'lon': lon,
        }

        if at_time is not None:
            if not isinstance(at_time, datetime.datetime):
                raise GeocoderQueryError(
                    "`at_time` must be an instance of `datetime.datetime`"
                )
            params['timestamp'] = timegm(at_time.utctimetuple())
        if self.api_key:
            params['key'] = self.api_key

        url = "?".join((self.timezone_api, urlencode(params)))
        logger.debug("%s.reverse_timezone: %s", self.__class__.__name__, url)
        return self._call_geocoder(url, self._parse_json_timezone, timeout=timeout)

    def _parse_place(self, place):
        location = place.get('formatted')
        latitude = place['lat']
        longitude = place['lon']
        return Location(location, (latitude, longitude), place)

    def _parse_json(self, page, exactly_one=True):
        places = page.get('results', [])
        if not places:
            return None

        if exactly_one:
            return self._parse_place(places[0])
        else:
            return [self._parse_place(place) for place in places]

    def _parse_suggestions(self, page, exactly_one=True):
        suggestions = page.get('suggestions', [])
        if not suggestions:
            return None

        def parse_suggestion(suggestion):
            return Location(
                suggestion.get('text'),
                (suggestion['lat'], suggestion['lon']),
                suggestion,
            )
        if exactly_one:
            return parse_suggestion(suggestions[0])
        else:
            return [parse_suggestion(suggestion) for suggestion in suggestions]

    def _parse_reverse_json(self, page, exactly_one=True):
        place = page.get('result')
        if not place:
            return None

        location = self._parse_place(place)
        if exactly_one:
            return location
        else:
            return [location]

    def _parse_json_timezone(self, response):
        return from_timezone_name(response['timezone'], raw=response)

    def _geocoder_exception_handler(self, error):
        if not isinstance(error, AdapterHTTPError):
            return
        if error.status_code is None or error.text is None:
            return
        try:
            message = json.loads(error.text)['error']['message']
        except (ValueError, KeyError, TypeError):
            message = error.text
        exc_cls = ERROR_CODE_MAP.get(error.status_code, GeocoderServiceError)
        if issubclass(exc_cls, GeocoderRateLimited):
            raise exc_cls(
                message, retry_after=get_retry_after(error.headers)
            ) from error
        raise exc_cls(message) from error
