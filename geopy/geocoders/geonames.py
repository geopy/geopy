import warnings

from geopy.compat import urlencode
from geopy.exc import (
    ConfigurationError,
    GeocoderInsufficientPrivileges,
    GeocoderServiceError,
)
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("GeoNames", )


class GeoNames(Geocoder):
    """GeoNames geocoder.

    Documentation at:
        http://www.geonames.org/export/geonames-search.html

    Reverse geocoding documentation at:
        http://www.geonames.org/export/web-services.html#findNearbyPlaceName
    """

    geocode_path = '/searchJSON'
    reverse_path = '/findNearbyPlaceNameJSON'

    def __init__(
            self,
            country_bias=None,
            username=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            format_string=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """
        :param str country_bias:

        :param str username: GeoNames username, required. Sign up here:
            http://www.geonames.org/login

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
        """
        super(GeoNames, self).__init__(
            format_string=format_string,
            scheme='http',
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )
        if username is None:
            raise ConfigurationError(
                'No username given, required for api access.  If you do not '
                'have a GeoNames username, sign up here: '
                'http://www.geonames.org/login'
            )
        self.username = username
        self.country_bias = country_bias
        domain = 'api.geonames.org'
        self.api = (
            "%s://%s%s" % (self.scheme, domain, self.geocode_path)
        )
        self.api_reverse = (
            "%s://%s%s" % (self.scheme, domain, self.reverse_path)
        )

    def geocode(self, query, exactly_one=True, timeout=DEFAULT_SENTINEL):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = {
            'q': self.format_string % query,
            'username': self.username
        }
        if self.country_bias:
            params['countryBias'] = self.country_bias
        if exactly_one:
            params['maxRows'] = 1
        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one,
        )

    def reverse(
            self,
            query,
            exactly_one=DEFAULT_SENTINEL,
            timeout=DEFAULT_SENTINEL,
    ):
        """
        Return an address by location point.

            .. versionadded:: 1.2.0

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

        try:
            lat, lng = self._coerce_point_to_string(query).split(',')
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")
        params = {
            'lat': lat,
            'lng': lng,
            'username': self.username
        }
        url = "?".join((self.api_reverse, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one
        )

    def _parse_json(self, doc, exactly_one):
        """
        Parse JSON response body.
        """
        places = doc.get('geonames', [])
        err = doc.get('status', None)
        if err and 'message' in err:
            if err['message'].startswith("user account not enabled to use"):
                raise GeocoderInsufficientPrivileges(err['message'])
            else:
                raise GeocoderServiceError(err['message'])
        if not len(places):
            return None

        def parse_code(place):
            """
            Parse each record.
            """
            latitude = place.get('lat', None)
            longitude = place.get('lng', None)
            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)
            else:
                return None

            placename = place.get('name')
            state = place.get('adminCode1', None)
            country = place.get('countryCode', None)

            location = ', '.join(
                [x for x in [placename, state, country] if x]
            )

            return Location(location, (latitude, longitude), place)

        if exactly_one:
            return parse_code(places[0])
        else:
            return [parse_code(place) for place in places]
