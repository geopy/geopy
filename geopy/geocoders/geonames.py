"""
:class:`GeoNames` geocoder.
"""

from geopy.compat import urlencode

from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT
from geopy.location import Location
from geopy.exc import (
    GeocoderInsufficientPrivileges,
    GeocoderServiceError,
    ConfigurationError
)
from geopy.util import logger


__all__ = ("GeoNames", )


class GeoNames(Geocoder): # pylint: disable=W0223
    """
    GeoNames geocoder, documentation at:
        http://www.geonames.org/export/geonames-search.html

    Reverse geocoding documentation at:
        http://www.geonames.org/maps/us-reverse-geocoder.html
    """

    def __init__(
            self,
            country_bias=None,
            username=None,
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
            user_agent=None,
        ):
        """
        :param str country_bias:

        :param str username:

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

            .. versionadded:: 0.97

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

            .. versionadded:: 0.96

        :param str user_agent: Use a custom User-Agent header.

            .. versionadded:: 1.12.0
        """
        super(GeoNames, self).__init__(
            scheme='http', timeout=timeout, proxies=proxies, user_agent=user_agent
        )
        if username is None:
            raise ConfigurationError(
                'No username given, required for api access.  If you do not '
                'have a GeoNames username, sign up here: '
                'http://www.geonames.org/login'
            )
        self.username = username
        self.country_bias = country_bias
        self.api = "%s://api.geonames.org/searchJSON" % self.scheme
        self.api_reverse = (
            "%s://api.geonames.org/findNearbyPlaceNameJSON" % self.scheme
        )

    def geocode(self, query, exactly_one=True, timeout=None): # pylint: disable=W0221
        """
        Geocode a location query.

        :param str query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

            .. versionadded:: 0.97
        """
        params = {
            'q': query,
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
            exactly_one=False,
            timeout=None,
        ):
        """
        Given a point, find an address.

            .. versionadded:: 1.2.0

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

        """
        try:
            lat, lng = [
                x.strip() for x in
                self._coerce_point_to_string(query).split(',')
            ]
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
