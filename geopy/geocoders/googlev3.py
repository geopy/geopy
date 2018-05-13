"""
:class:`.GoogleV3` is the Google Maps V3 geocoder.
"""

import base64
import hashlib
import hmac
import warnings

from geopy.compat import urlencode
from geopy.exc import (
    ConfigurationError,
    GeocoderParseError,
    GeocoderQueryError,
    GeocoderQuotaExceeded,
)
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

try:
    from pytz import timezone, UnknownTimeZoneError
    from calendar import timegm
    from datetime import datetime
    from numbers import Number
    pytz_available = True
except ImportError:
    pytz_available = False


__all__ = ("GoogleV3", )


class GoogleV3(Geocoder):  # pylint: disable=R0902
    """Geocoder using the Google Maps v3 API.

    Documentation at:
        https://developers.google.com/maps/documentation/geocoding/

    API authentication is only required for Google Maps Premier customers.
    """

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

        self.api_key = api_key
        self.domain = domain.strip('/')

        self.premier = bool(client_id and secret_key)
        self.client_id = client_id
        self.secret_key = secret_key
        self.channel = channel

        self.api = '%s://%s/maps/api/geocode/json' % (self.scheme, self.domain)
        self.tz_api = '%s://%s/maps/api/timezone/json' % (
            self.scheme,
            self.domain
        )

    def _get_signed_url(self, params):
        """
        Returns a Premier account signed url. Docs on signature:
            https://developers.google.com/maps/documentation/business/webservices/auth#digital_signatures
        """
        params['client'] = self.client_id

        if self.channel:
            params['channel'] = self.channel

        path = "?".join(('/maps/api/geocode/json', urlencode(params)))
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
            (":".join(item)
             for item in components.items()
            )
        )

    @staticmethod
    def _format_bounds_param(bounds):
        """
        Format the bounds to something Google understands.
        """
        return '%f,%f|%f,%f' % (bounds[0], bounds[1], bounds[2], bounds[3])

    def geocode(
            self,
            query=None,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            bounds=None,
            region=None,
            components=None,
            language=None,
            sensor=False,
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode. Optional,
            if ``components`` param is set::

                >>> g = GoogleV3()
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

        :param bounds: The bounding box of the viewport within which
            to bias geocode results more prominently.
        :type bounds: list or tuple

        :param str region: The region code, specified as a ccTLD
            ("top-level domain") two-character value.

        :param dict components: Restricts to an area. Can use any combination
            of: route, locality, administrative_area, postal_code, country.

        :param str language: The language in which to return results.

        :param bool sensor: Whether the geocoding request comes from a
            device with a location sensor.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = {
            'sensor': str(sensor).lower()
        }
        if query is None and not components:
            raise ValueError('Either `query` or `components` must be set.`')
        if query is not None:
            params['address'] = self.format_string % query
        if self.api_key:
            params['key'] = self.api_key
        if bounds:
            if len(bounds) != 4:
                raise GeocoderQueryError(
                    "bounds must be a four-item iterable of lat,lon,lat,lon"
                )
            params['bounds'] = self._format_bounds_param(bounds)
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
                          DeprecationWarning)
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
        **This is an unstable API.**

        Finds the timezone a `location` was in for a specified `at_time`,
        and returns a pytz timezone object.

            .. versionadded:: 1.2.0

        :param location: The coordinates for which you want a timezone.
        :type location: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param at_time: The time at which you want the timezone of this
            location. This is optional, and defaults to the time that the
            function is called in UTC.
        :type at_time: int or float or datetime

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: pytz timezone. See :func:`pytz.timezone`.
        """
        if not pytz_available:
            raise ImportError(
                'pytz must be installed in order to locate timezones. '
                ' Install with `pip install geopy -e ".[timezone]"`.'
            )
        location = self._coerce_point_to_string(location)

        if isinstance(at_time, Number):
            timestamp = at_time
        elif isinstance(at_time, datetime):
            timestamp = timegm(at_time.utctimetuple())
        elif at_time is None:
            timestamp = timegm(datetime.utcnow().utctimetuple())
        else:
            raise GeocoderQueryError(
                "`at_time` must be an epoch integer or "
                "datetime.datetime object"
            )

        params = {
            "location": location,
            "timestamp": timestamp,
        }
        if self.api_key:
            params['key'] = self.api_key
        url = "?".join((self.tz_api, urlencode(params)))

        logger.debug("%s.timezone: %s", self.__class__.__name__, url)
        response = self._call_geocoder(url, timeout=timeout)

        try:
            tz = timezone(response["timeZoneId"])
        except UnknownTimeZoneError:
            raise GeocoderParseError(
                "pytz could not parse the timezone identifier (%s) "
                "returned by the service." % response["timeZoneId"]
            )
        except KeyError:
            raise GeocoderParseError(
                "geopy could not find a timezone in this response: %s" %
                response
            )
        return tz

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
