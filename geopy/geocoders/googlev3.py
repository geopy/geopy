"""
:class:`.GoogleV3` is the Google Maps V3 geocoder.
"""

import base64
import hashlib
import hmac
from geopy.compat import urlencode
from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT, DEFAULT_SCHEME
from geopy.exc import (
    GeocoderQueryError,
    GeocoderQuotaExceeded,
    ConfigurationError,
    GeocoderParseError,
    GeocoderQueryError,
)
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
    """
    Geocoder using the Google Maps v3 API. Documentation at:
        https://developers.google.com/maps/documentation/geocoding/
    """

    def __init__(
            self,
            api_key=None,
            domain='maps.googleapis.com',
            scheme=DEFAULT_SCHEME,
            client_id=None,
            secret_key=None,
            timeout=DEFAULT_TIMEOUT,
            proxies=None
        ):  # pylint: disable=R0913
        """
        Initialize a customized Google geocoder.

        API authentication is only required for Google Maps Premier customers.

        :param string api_key: The API key required by Google to perform
            geocoding requests. API keys are managed through the Google APIs
            console (https://code.google.com/apis/console).

            .. versionadded:: 0.98.2

        :param string domain: Should be the localized Google Maps domain to
            connect to. The default is 'maps.google.com', but if you're
            geocoding address in the UK (for example), you may want to set it
            to 'maps.google.co.uk' to properly bias results.

        :param string scheme: Use 'https' or 'http' as the API URL's scheme.
            Default is https. Note that SSL connections' certificates are not
            verified.

            .. versionadded:: 0.97

        :param string client_id: If using premier, the account client id.

        :param string secret_key: If using premier, the account secret key.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

            .. versionadded:: 0.96
        """
        super(GoogleV3, self).__init__(
            scheme=scheme, timeout=timeout, proxies=proxies
        )
        if client_id and not secret_key:
            raise ConfigurationError('Must provide secret_key with client_id.')
        if secret_key and not client_id:
            raise ConfigurationError('Must provide client_id with secret_key.')

        self.api_key = api_key
        self.domain = domain.strip('/')
        self.scheme = scheme
        self.doc = {}

        if client_id and secret_key:
            self.premier = True
            self.client_id = client_id
            self.secret_key = secret_key
        else:
            self.premier = False
            self.client_id = None
            self.secret_key = None

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

    def geocode(
            self,
            query,
            exactly_one=True,
            timeout=None,
            bounds=None,
            region=None,
            components=None,
            language=None,
            sensor=False,
        ):  # pylint: disable=W0221,R0913
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

            .. versionadded:: 0.97

        :param bounds: The bounding box of the viewport within which
            to bias geocode results more prominently.
        :type bounds: list or tuple

        :param string region: The region code, specified as a ccTLD
            ("top-level domain") two-character value.

        :param dict components: Restricts to an area. Can use any combination
            of: route, locality, administrative_area, postal_code, country.

            .. versionadded:: 0.97.1

        :param string language: The language in which to return results.

        :param bool sensor: Whether the geocoding request comes from a
            device with a location sensor.
        """
        params = {
            'address': self.format_string % query,
            'sensor': str(sensor).lower()
        }
        if self.api_key:
            params['key'] = self.api_key
        if bounds:
            params['bounds'] = bounds
        if region:
            params['region'] = region
        if components:
            params['components'] = self._format_components_param(components)
        if language:
            params['language'] = language

        if self.premier is False:
            url = "?".join((self.api, urlencode(params)))
        else:
            url = self._get_signed_url(params)

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    def reverse(
            self,
            query,
            exactly_one=False,
            timeout=None,
            language=None,
            sensor=False,
        ):  # pylint: disable=W0221,R0913
        """
        Given a point, find an address.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param boolean exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

            .. versionadded:: 0.97

        :param string language: The language in which to return results.

        :param boolean sensor: Whether the geocoding request comes from a
            device with a location sensor.
        """
        params = {
            'latlng': self._coerce_point_to_string(query),
            'sensor': str(sensor).lower()
        }
        if language:
            params['language'] = language

        if not self.premier:
            url = "?".join((self.api, urlencode(params)))
        else:
            url = self._get_signed_url(params)

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    def timezone(self, location, at_time=None, timeout=None):
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
        :type at_time integer, long, float, datetime:

        :rtype: pytz timezone
        """
        if not pytz_available:
            raise ImportError(
                u'pytz must be installed in order to locate timezones. '
                u' Install with `pip install geopy -e ".[timezone]"`.'
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
                u"`at_time` must be an epoch integer or "
                u"datetime.datetime object"
            )

        params = {
            u"location": location,
            u"timestamp": timestamp,
        }
        url = u"?".join((self.tz_api, urlencode(params)))

        logger.debug("%s.timezone: %s", self.__class__.__name__, url)
        response = self._call_geocoder(url, timeout=timeout)

        try:
            tz = timezone(response["timeZoneId"])
        except UnknownTimeZoneError:
            raise GeocoderParseError(
                u"pytz could not parse the timezone identifier (%s) "
                u"returned by the service." % response["timeZoneId"]
            )
        except KeyError:
            raise GeocoderParseError(
                u"geopy could not find a timezone in this response: %s" %
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

