"""
:class:`.ArcGIS` geocoder.
"""

import json
from time import time
from geopy.compat import urlencode, Request

from geopy.geocoders.base import Geocoder, DEFAULT_SCHEME, DEFAULT_TIMEOUT, \
    DEFAULT_WKID
from geopy.exc import GeocoderServiceError, GeocoderAuthenticationFailure
from geopy.exc import ConfigurationError
from geopy.location import Location
from geopy.util import logger


__all__ = ("ArcGIS", )


class ArcGIS(Geocoder):  # pylint: disable=R0921,R0902,W0223
    """
    Geocoder using the ERSI ArcGIS API. Documentation at:
        https://developers.arcgis.com/rest/geocode/api-reference/overview-world-geocoding-service.htm
    """

    _TOKEN_EXPIRED = 498
    _MAX_RETRIES = 3
    auth_api = 'https://www.arcgis.com/sharing/generateToken'

    def __init__(self, username=None, password=None, referer=None, # pylint: disable=R0913
                 token_lifetime=60, scheme=DEFAULT_SCHEME,
                 timeout=DEFAULT_TIMEOUT, proxies=None,
                 user_agent=None):
        """
        Create a ArcGIS-based geocoder.

            .. versionadded:: 0.97

        :param str username: ArcGIS username. Required if authenticated
            mode is desired.

        :param str password: ArcGIS password. Required if authenticated
            mode is desired.

        :param str referer: Required if authenticated mode is desired.
            'Referer' HTTP header to send with each request,
            e.g., 'http://www.example.com'. This is tied to an issued token,
            so fielding queries for multiple referrers should be handled by
            having multiple ArcGIS geocoder instances.

        :param int token_lifetime: Desired lifetime, in minutes, of an
            ArcGIS-issued token.

        :param str scheme: Desired scheme. If authenticated mode is in use,
            it must be 'https'.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

        :param str user_agent: Use a custom User-Agent header.

            .. versionadded:: 1.12.0
        """
        super(ArcGIS, self).__init__(
            scheme=scheme, timeout=timeout, proxies=proxies, user_agent=user_agent
        )
        if username or password or referer:
            if not (username and password and referer):
                raise ConfigurationError(
                    "Authenticated mode requires username,"
                    " password, and referer"
                )
            if self.scheme != 'https':
                raise ConfigurationError(
                    "Authenticated mode requires scheme of 'https'"
                )
            self._base_call_geocoder = self._call_geocoder
            self._call_geocoder = self._authenticated_call_geocoder

        self.username = username
        self.password = password
        self.referer = referer

        self.token = None
        self.token_lifetime = token_lifetime * 60 # store in seconds
        self.token_expiry = None
        self.retry = 1

        self.api = (
            '%s://geocode.arcgis.com/arcgis/rest/services/'
            'World/GeocodeServer/find' % self.scheme
        )
        self.reverse_api = (
            '%s://geocode.arcgis.com/arcgis/rest/services/'
            'World/GeocodeServer/reverseGeocode' % self.scheme
        )

    def _authenticated_call_geocoder(self, url, timeout=None):
        """
        Wrap self._call_geocoder, handling tokens.
        """
        if self.token is None or int(time()) > self.token_expiry:
            self._refresh_authentication_token()
        request = Request(
            "&".join((url, urlencode({"token": self.token}))),
            headers={"Referer": self.referer}
        )
        return self._base_call_geocoder(request, timeout=timeout)

    def geocode(self, query, exactly_one=True, timeout=None):
        """
        Geocode a location query.

        :param str query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.
        """
        params = {'text': query, 'f': 'json'}
        if exactly_one:
            params['maxLocations'] = 1
        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        response = self._call_geocoder(url, timeout=timeout)

        # Handle any errors; recursing in the case of an expired token.
        if 'error' in response:
            if response['error']['code'] == self._TOKEN_EXPIRED:
                self.retry += 1
                self._refresh_authentication_token()
                return self.geocode(
                    query, exactly_one=exactly_one, timeout=timeout
                )
            raise GeocoderServiceError(str(response['error']))

        # Success; convert from the ArcGIS JSON format.
        if not len(response['locations']):
            return None
        geocoded = []
        for resource in response['locations']:
            geometry = resource['feature']['geometry']
            geocoded.append(
                Location(
                    resource['name'], (geometry['y'], geometry['x']), resource
                )
            )
        if exactly_one:
            return geocoded[0]
        return geocoded

    def reverse(self, query, exactly_one=True, timeout=None, # pylint: disable=R0913,W0221
                distance=None, wkid=DEFAULT_WKID):
        """
        Given a point, find an address.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s".

        :param bool exactly_one: Return one result, or a list?

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param int distance: Distance from the query location, in meters,
            within which to search. ArcGIS has a default of 100 meters, if not
            specified.

        :param str wkid: WKID to use for both input and output coordinates.
        """
        # ArcGIS is lon,lat; maintain lat,lon convention of geopy
        point = self._coerce_point_to_string(query).split(",")
        if wkid != DEFAULT_WKID:
            location = {"x": point[1], "y": point[0], "spatialReference": wkid}
        else:
            location = ",".join((point[1], point[0]))
        params = {'location': location, 'f': 'json', 'outSR': wkid}
        if distance is not None:
            params['distance'] = distance
        url = "?".join((self.reverse_api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        response = self._call_geocoder(url, timeout=timeout)
        if not len(response):
            return None
        if 'error' in response:
            if response['error']['code'] == self._TOKEN_EXPIRED:
                self.retry += 1
                self._refresh_authentication_token()
                return self.reverse(query, exactly_one=exactly_one,
                                    timeout=timeout, distance=distance,
                                    wkid=wkid)
            raise GeocoderServiceError(str(response['error']))
        address = (
            "%(Address)s, %(City)s, %(Region)s %(Postal)s,"
            " %(CountryCode)s" % response['address']
        )
        return Location(
            address,
            (response['location']['y'], response['location']['x']),
            response['address']
        )

    def _refresh_authentication_token(self):
        """
        POST to ArcGIS requesting a new token.
        """
        if self.retry == self._MAX_RETRIES:
            raise GeocoderAuthenticationFailure(
                'Too many retries for auth: %s' % self.retry
            )
        token_request_arguments = {
            'username': self.username,
            'password': self.password,
            'referer': self.referer,
            'expiration': self.token_lifetime,
            'f': 'json'
        }
        url = "?".join((self.auth_api, urlencode(token_request_arguments)))
        logger.debug(
            "%s._refresh_authentication_token: %s",
            self.__class__.__name__, url
        )
        self.token_expiry = int(time()) + self.token_lifetime
        response = self._base_call_geocoder(url)
        if 'token' not in response:
            raise GeocoderAuthenticationFailure(
                'Missing token in auth request.'
                'Request URL: %s; response JSON: %s' %
                (url, json.dumps(response))
            )
        self.retry = 0
        self.token = response['token']
