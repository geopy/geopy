import base64
import hashlib
import hmac
import warnings
from calendar import timegm
from datetime import datetime
from numbers import Number

from geopy.compat import urlencode
from geopy.exc import ConfigurationError, GeocoderQueryError, GeocoderQuotaExceeded
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.timezone import ensure_pytz_is_installed, from_timezone_name
from geopy.util import logger

__all__ = ("GoogleV3", )


class GoogleV3(Geocoder):
    """Geocoder using the Google Maps v3 API.

    Documentation at:
        https://developers.google.com/maps/documentation/geocoding/

    .. attention::
        Since July 2018 Google requires each request to have an API key.
        See https://developers.google.com/maps/documentation/geocoding/usage-and-billing
    """

    api_path = '/maps/api/geocode/json'
    timezone_path = '/maps/api/timezone/json'

    def __init__(
            self,
            api_key=None,
            domain='maps.googleapis.com',
            scheme=None,
            client_id=None,
            secret_key=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            format_string=None,
            ssl_context=DEFAULT_SENTINEL,
            channel='',
    ):
        """

        :param str api_key: The API key required by Google to perform
            geocoding requests. API keys are managed through the Google APIs
            console (https://code.google.com/apis/console).
            Make sure to have both ``Geocoding API`` and ``Time Zone API``
            services enabled for this API key.

        :param str domain: Should be the localized Google Maps domain to
            connect to. The default is 'maps.googleapis.com', but if you're
            geocoding address in the UK (for example), you may want to set it
            to 'maps.google.co.uk' to properly bias results.

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`.

        :param str client_id: If using premier, the account client id.

        :param str secret_key: If using premier, the account secret key.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str user_agent:
            See :attr:`geopy.geocoders.options.default_user_agent`.

            .. versionadded:: 1.12.0

        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

            .. versionadded:: 1.14.0

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.

            .. versionadded:: 1.14.0

        :param str channel: If using premier, the channel identifier.

            .. versionadded:: 1.12.0
        """
        super(GoogleV3, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )
        if client_id and not secret_key:
            raise ConfigurationError('Must provide secret_key with client_id.')
        if secret_key and not client_id:
            raise ConfigurationError('Must provide client_id with secret_key.')

        self.premier = bool(client_id and secret_key)
        self.client_id = client_id
        self.secret_key = secret_key

        if not self.premier and not api_key:
            warnings.warn(
                'Since July 2018 Google requires each request to have an API key. '
                'Pass a valid `api_key` to GoogleV3 geocoder to hide this warning. '
                'See https://developers.google.com/maps/documentation/geocoding/usage-and-billing',  # noqa
                UserWarning,
                stacklevel=2
            )

        self.api_key = api_key
        self.domain = domain.strip('/')

        self.channel = channel

        self.api = '%s://%s%s' % (self.scheme, self.domain, self.api_path)
        self.tz_api = '%s://%s%s' % (self.scheme, self.domain, self.timezone_path)

    def _get_signed_url(self, params):
        """
        Returns a Premier account signed url. Docs on signature:
            https://developers.google.com/maps/documentation/business/webservices/auth#digital_signatures
        """
        params['client'] = self.client_id

        if self.channel:
            params['channel'] = self.channel

        path = "?".join((self.api_path, urlencode(params)))
        signature = hmac.new(
            base64.urlsafe_b64decode(self.secret_key),
            path.encode('utf-8'),
            hashlib.sha1
        )
        signature = base64.urlsafe_b64encode(
            signature.digest()
        ).decode('utf-8')
        return '%s://%s%s&signature=%s' % (
            self.scheme, self.domain, path, signature
        )

    @staticmethod
    def _format_components_param(components):
        """
        Format the components dict to something Google understands.
        """
        return "|".join(
            (":".join(item) for item in components.items())
        )

    def geocode(
            self,
            query=None,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            bounds=None,
            region=None,
            components=None,
            place_id=None,
            language=None,
            sensor=False,
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode. Optional,
            if ``components`` param is set::

                >>> g.geocode(components={"city": "Paris", "country": "FR"})
                Location(France, (46.227638, 2.213749, 0.0))

            .. versionchanged:: 1.14.0
               Now ``query`` is optional if ``components`` param is set.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :type bounds: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.
        :param bounds: The bounding box of the viewport within which
            to bias geocode results more prominently.
            Example: ``[Point(22, 180), Point(-22, -180)]``.

            .. versionchanged:: 1.17.0
                Previously the only supported format for bounds was a
                list like ``[latitude, longitude, latitude, longitude]``.
                This format is now deprecated in favor of a list/tuple
                of a pair of geopy Points and will be removed in geopy 2.0.

        :param str region: The region code, specified as a ccTLD
            ("top-level domain") two-character value.

        :param dict components: Restricts to an area. Can use any combination
            of: route, locality, administrative_area, postal_code, country.

        :param str place_id: Retrieve a Location using a Place ID.
            Cannot be not used with ``query`` or ``bounds`` parameters.

                >>> g.geocode(place_id='ChIJOcfP0Iq2j4ARDrXUa7ZWs34')

            .. versionadded:: 1.19.0

        :param str language: The language in which to return results.

        :param bool sensor: Whether the geocoding request comes from a
            device with a location sensor.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = {
            'sensor': str(sensor).lower()
        }
        if place_id and (bounds or query):
            raise ValueError(
                'Only one of the `query` or `place id` or `bounds` '
                ' parameters must be entered.')

        if place_id is not None:
            params['place_id'] = place_id

        if query is not None:
            params['address'] = self.format_string % query

        if query is None and place_id is None and not components:
            raise ValueError('Either `query` or `components` or `place_id` '
                             'must be set.')

        if self.api_key:
            params['key'] = self.api_key
        if bounds:
            if len(bounds) == 4:
                warnings.warn(
                    'GoogleV3 `bounds` format of '
                    '`[latitude, longitude, latitude, longitude]` is now '
                    'deprecated and will not be supported in geopy 2.0. '
                    'Use `[Point(latitude, longitude), Point(latitude, longitude)]` '
                    'instead.',
                    DeprecationWarning,
                    stacklevel=2
                )
                lat1, lon1, lat2, lon2 = bounds
                bounds = [[lat1, lon1], [lat2, lon2]]
            params['bounds'] = self._format_bounding_box(
                bounds, "%(lat1)s,%(lon1)s|%(lat2)s,%(lon2)s")
        if region:
            params['region'] = region
        if components:
            params['components'] = self._format_components_param(components)
        if language:
            params['language'] = language

        if self.premier:
            url = self._get_signed_url(params)
        else:
            url = "?".join((self.api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    def reverse(
            self,
            query,
            exactly_one=DEFAULT_SENTINEL,
            timeout=DEFAULT_SENTINEL,
            language=None,
            sensor=False,
    ):
        """
        Return an address by location point.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param bool exactly_one: Return one result or a list of results, if
            available.

            .. versionchanged:: 1.14.0
               Default value for ``exactly_one`` was ``False``, which differs
               from the conventional default across geopy. Please always pass
               this argument explicitly, otherwise you would get a warning.
               In geopy 2.0 the default value will become ``True``.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param str language: The language in which to return results.

        :param bool sensor: Whether the geocoding request comes from a
            device with a location sensor.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        if exactly_one is DEFAULT_SENTINEL:
            warnings.warn('%s.reverse: default value for `exactly_one` '
                          'argument will become True in geopy 2.0. '
                          'Specify `exactly_one=False` as the argument '
                          'explicitly to get rid of this warning.' % type(self).__name__,
                          DeprecationWarning, stacklevel=2)
            exactly_one = False

        params = {
            'latlng': self._coerce_point_to_string(query),
            'sensor': str(sensor).lower()
        }
        if language:
            params['language'] = language
        if self.api_key:
            params['key'] = self.api_key

        if not self.premier:
            url = "?".join((self.api, urlencode(params)))
        else:
            url = self._get_signed_url(params)

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    def timezone(self, location, at_time=None, timeout=DEFAULT_SENTINEL):
        """
        Find the timezone a `location` was in for a specified `at_time`,
        and return a pytz timezone object.

        .. versionadded:: 1.2.0

        .. deprecated:: 1.18.0
           Use :meth:`GoogleV3.reverse_timezone` instead. This method
           will be removed in geopy 2.0.

        .. versionchanged:: 1.18.1
           Previously a :class:`KeyError` was raised for a point without
           an assigned Olson timezone id (e.g. for Antarctica).
           Now this method returns None for such requests.

        :param location: The coordinates for which you want a timezone.
        :type location: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param at_time: The time at which you want the timezone of this
            location. This is optional, and defaults to the time that the
            function is called in UTC. Timezone-aware datetimes are correctly
            handled and naive datetimes are silently treated as UTC.

            .. versionchanged:: 1.18.0
               Previously this parameter accepted raw unix timestamp as
               int or float. This is now deprecated in favor of datetimes
               and support for numbers will be removed in geopy 2.0.

        :type at_time: :class:`datetime.datetime` or None

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None`` or pytz timezone. See :func:`pytz.timezone`.
        """

        warnings.warn('%(cls)s.timezone method is deprecated in favor of '
                      '%(cls)s.reverse_timezone, which returns geopy.Timezone '
                      'object containing pytz timezone and a raw response '
                      'instead of just pytz timezone. This method will '
                      'be removed in geopy 2.0.' % dict(cls=type(self).__name__),
                      DeprecationWarning, stacklevel=2)
        timezone = self.reverse_timezone(location, at_time, timeout)
        if timezone is None:
            return None
        return timezone.pytz_timezone

    def reverse_timezone(self, query, at_time=None, timeout=DEFAULT_SENTINEL):
        """
        Find the timezone a point in `query` was in for a specified `at_time`.

        .. versionadded:: 1.18.0

        .. versionchanged:: 1.18.1
           Previously a :class:`KeyError` was raised for a point without
           an assigned Olson timezone id (e.g. for Antarctica).
           Now this method returns None for such requests.

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

        :rtype: ``None`` or :class:`geopy.timezone.Timezone`
        """
        ensure_pytz_is_installed()

        location = self._coerce_point_to_string(query)

        timestamp = self._normalize_timezone_at_time(at_time)

        params = {
            "location": location,
            "timestamp": timestamp,
        }
        if self.api_key:
            params['key'] = self.api_key
        url = "?".join((self.tz_api, urlencode(params)))

        logger.debug("%s.reverse_timezone: %s", self.__class__.__name__, url)
        return self._parse_json_timezone(
            self._call_geocoder(url, timeout=timeout)
        )

    def _parse_json_timezone(self, response):
        status = response.get('status')
        if status != 'OK':
            self._check_status(status)

        timezone_id = response.get("timeZoneId")
        if timezone_id is None:
            # Google returns `status: ZERO_RESULTS` for uncovered
            # points (e.g. for Antarctica), so there's nothing
            # meaningful to be returned as the `raw` response,
            # hence we return `None`.
            return None
        return from_timezone_name(timezone_id, raw=response)

    def _normalize_timezone_at_time(self, at_time):
        if at_time is None:
            timestamp = timegm(datetime.utcnow().utctimetuple())
        elif isinstance(at_time, Number):
            warnings.warn(
                'Support for `at_time` as int/float is deprecated '
                'and will be removed in geopy 2.0. '
                'Pass a `datetime.datetime` instance instead.',
                DeprecationWarning,
                stacklevel=3
            )
            timestamp = at_time
        elif isinstance(at_time, datetime):
            # Naive datetimes are silently treated as UTC.
            # Timezone-aware datetimes are handled correctly.
            timestamp = timegm(at_time.utctimetuple())
        else:
            raise GeocoderQueryError(
                "`at_time` must be an instance of `datetime.datetime`"
            )
        return timestamp

    def _parse_json(self, page, exactly_one=True):
        '''Returns location, (latitude, longitude) from json feed.'''

        places = page.get('results', [])
        if not len(places):
            self._check_status(page.get('status'))
            return None

        def parse_place(place):
            '''Get the location, lat, lng from a single json place.'''
            location = place.get('formatted_address')
            latitude = place['geometry']['location']['lat']
            longitude = place['geometry']['location']['lng']
            return Location(location, (latitude, longitude), place)

        if exactly_one:
            return parse_place(places[0])
        else:
            return [parse_place(place) for place in places]

    @staticmethod
    def _check_status(status):
        """
        Validates error statuses.
        """
        if status == 'ZERO_RESULTS':
            # When there are no results, just return.
            return
        if status == 'OVER_QUERY_LIMIT':
            raise GeocoderQuotaExceeded(
                'The given key has gone over the requests limit in the 24'
                ' hour period or has submitted too many requests in too'
                ' short a period of time.'
            )
        elif status == 'REQUEST_DENIED':
            raise GeocoderQueryError(
                'Your request was denied.'
            )
        elif status == 'INVALID_REQUEST':
            raise GeocoderQueryError('Probably missing address or latlng.')
        else:
            raise GeocoderQueryError('Unknown error.')
