"""
:class:`.ArcGIS` geocoder.
"""

import json
from time import time
from geopy.compat import urlencode
from urllib2 import Request

from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT
from geopy.exc import GeocoderError, GeocoderAuthenticationFailure
from geopy.exc import ConfigurationError
from geopy.util import logger


class ArcGIS(Geocoder): # pylint: disable=R0921,R0902
    """
    Geocoder using the ERSI ArcGIS API. Documentation at:
        http://resources.arcgis.com/en/help/arcgis-rest-api
    """

    _TOKEN_EXPIRED = 498
    _MAX_RETRIES = 3
    auth_api = 'https://www.arcgis.com/sharing/generateToken'
    api = 'https://geocode.arcgis.com' \
                '/arcgis/rest/services/World/GeocodeServer/find'
    reverse_api = 'https://geocode.arcgis.com' \
                '/arcgis/rest/services/World/GeocodeServer/reverseGeocode'

    def __init__(self, username=None, password=None, referer=None, # pylint: disable=R0913
                 token_lifetime=60,
                 timeout=DEFAULT_TIMEOUT, proxies=None):
        """
        Create a ArcGIS-based geocoder.

            .. versionadded:: 0.97

        ArcGIS requires an HTTPS connection for generating tokens,
        so this geocoder does not accept a `scheme` argument setting the
        use of HTTP or HTTPS.

        :param string username: If specified, username and password are used
        to generate authentication
        tokens which are then used for each geocode request. If the token
        expires, another one is generated.

        :param string password: See username.

        :param string referer: 'Referer' HTTP header to send with each request,
            e.g., 'http://www.example.com'. This is tied to an issued token,
            so fielding queries for multiple referers should be handled by
            having multiple ArcGIS geocoder instances.

        :param int token_lifetime: Lifetime, in minutes, of an ArcGIS-issued
            token.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.
        """
        super(ArcGIS, self).__init__(timeout=timeout)
        if (username or password or referer):
            if not (username and password and referer):
                raise ConfigurationError(
                    'Authenticated mode requires username, password, and referer'
                )
            self._base_call_geocoder = self._call_geocoder
            self._call_geocoder = self._authenticated_call_geocoder
        self.username = username
        self.password = password
        self.referer = referer

        # It is tempting to get an authentication token at this point; however,
        # if you do, it risks throwing an exception at startup for any service
        # that instantiaties a ArcGIS geocoder. Instead, lazily get a token.
        self.token = None
        self.token_lifetime = token_lifetime * 60 # store in seconds
        self.token_expiry = None
        self.retry = 1
        if username:
            self.token = 'fake'  # This will fail and trigger re-authentication.

    def _authenticated_call_geocoder(self, url, timeout=None):
        """
        Wrap self._call_geocoder, handling tokens.
        """
        if self.token is None or int(time()) > self.token_expiry:
            self._refresh_authentication_token()
        request = Request("&token=".join((url, self.token))) # no urlencoding
        request.add_header('Referer', self.referer)
        return self._base_call_geocoder(request, timeout=timeout)

    def geocode(self, query, exactly_one=True, timeout=None):
        params = {'text': query, 'f': 'json'}
        if exactly_one is True:
            params['maxLocations'] = 1
        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        response = self._call_geocoder(url, timeout=timeout)

        # Handle any errors; recursing in the case of an expired token.
        if 'error' in response:
            if response['error']['code'] == self._TOKEN_EXPIRED:
                # Authentication token is expired or old; make a new one.
                self.retry += 1
                self._refresh_authentication_token()
                return self.geocode(query, exactly_one=exactly_one, timeout=timeout)
            raise GeocoderError(
                'Got unknown error from ArcGIS. '
                'Request URL: %s; response JSON: %s' %
                (url, json.dumps(response))
            )

        # Success; convert from the ArcGIS JSON format.
        if not len(response['locations']):
            return None
        geocoded = []
        for resource in response['locations']:
            geometry = resource['feature']['geometry']
            geocoded.append((resource['name'], (geometry['y'], geometry['x'])))
        if exactly_one is True:
            return geocoded[0]
        return geocoded

    def reverse(self, query, exactly_one=True, timeout=None):
        """
        ArcGIS has an API for this, so TODO:
            http://resources.arcgis.com/en/help/arcgis-rest-api/index.html#//02r30000000n000000
            http://resources.arcgis.com/en/help/rest/apiref/index.html?reverse.html
        """
        raise NotImplementedError()

    def _refresh_authentication_token(self):
        """
        POST to ArcGIS requesting a new token.
        """
        if self.retry == self._MAX_RETRIES:
            logger.debug('Maximum retries (%s) reached; giving up.', self._MAX_RETRIES)
            raise GeocoderAuthenticationFailure(
                'Too many retries for auth: %s' % self.retry
            )
        token_request_arguments = {
            'username': self.username,
            'password': self.password,
            'expiration': self.token_lifetime,
            'f': 'json'
        }
        token_request_arguments = "&".join(
            ["%s=%s" % (key, val) for key, val in token_request_arguments.items()]
        )
        url = "&".join((
            "?".join((self.auth_api, token_request_arguments)),
            urlencode({'referer': self.referer})
        ))
        logger.debug(
            "%s._refresh_authentication_token: %s", self.__class__.__name__, url
        )
        self.token_expiry = int(time()) + self.token_lifetime
        response = self._base_call_geocoder(url)
        if not 'token' in response:
            raise GeocoderAuthenticationFailure(
                'Missing token in auth request.'
                'Request URL: %s; response JSON: %s' %
                (url, json.dumps(response))
            )
        self.retry = 0
        self.token = response['token']
