try:
    import json
except ImportError:
    import simplejson as json

from urllib import urlencode
from urllib2 import urlopen, Request

from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT
from geopy.exc import GeocoderError, GeocoderAuthenticationFailure
from geopy.exc import ConfigurationError
from geopy.util import logger, decode_page


_TOKEN_EXPIRED = 498
_REQUEST_AUTHENTICATION_URL = 'https://www.arcgis.com/sharing/generateToken?%s'
_GEOCODE_URL = ('https://geocode.arcgis.com/'
                'arcgis/rest/services/World/GeocodeServer/find?%s')
_MAX_RETRIES = 3


class ArcGIS(Geocoder):
    """Geocoder using the ERSI ArcGIS API"""

    def __init__(self, username=None, password=None, referer=None,
                 requested_token_lifetime_minutes=60):
        """Create a ArcGIS-based geocoder

        If specified, username and password are used to generate authentication
        tokens which are then used for each geocode request. If the token
        expires, another one is generated. The referer is only needed due to
        ESRI requiring that the requesting referer match the one for the
        authentication token; it is effectively ignored (but is required for
        authenticated queries)."""
        self.username = username
        self.password = password
        self.referer = referer
        self.requested_token_lifetime_minutes = requested_token_lifetime_minutes
        # It is tempting to get an authentication token at this point; however,
        # if you do, it risks throwing an exception at startup for any service
        # that instantiaties a ArcGIS geocoder. Instead, lazily get a token.
        self.token = None
        if username:
            self.token = 'fake'  # This will fail and trigger re-authentication.

        if username and not referer:
            raise ConfigurationError(
                'Must have a referer to use authenticated mode')

    def geocode(self, string, exactly_one=False, retry=0,
                timeout=DEFAULT_TIMEOUT):
        if retry == _MAX_RETRIES:
            log.debug('Maximum retries (%s) reached; giving up.' % _MAX_RETRIES)
            raise GeocoderAuthenticationFailure(
                'Too many retries for auth: %s' % retry)

        if isinstance(string, unicode):
            string = string.encode('utf-8')

        params = {'text': string, 'f': 'pjson'}
        if self.token:
            params['token'] = self.token
        url = _GEOCODE_URL % urlencode(params)

        # Hit the geocoding service.
        logger.debug("Fetching %s..." % url)
        response = json.loads(self._fetch(url, timeout=timeout))

        # Handle any errors; recursing in the case of an expired token.
        if 'error' in response:
            if response['error']['code'] == _TOKEN_EXPIRED:
                # Authentication token is expired or old; make a new one.
                self._refresh_authentication_token()
                return self.geocode(string, retry=retry + 1,
                                    exactly_one=exactly_one, timeout=timeout)
            raise GeocoderError('Got unknown error from ArcGIS. '
                                'Request URL: %s; response JSON: %s' %
                                (url, json.dumps(response)))

        # Success; convert from the ArcGIS JSON format.
        geocoded = []
        for resource in response['locations']:
            geometry = resource['feature']['geometry']
            geocoded.append((resource['name'], (geometry['y'], geometry['x'])))
        logger.debug('Got %s results' % len(geocoded))
        if exactly_one:
            return geocoded[0] if len(geocoded) else None
        return geocoded

    def _fetch(self, url, timeout=None):
        request = Request(url)

        # ArcGIS expects the referer to match the one given when creating the
        # geocoder authentication token.
        if self.referer:
            request.add_header('Referer', self.referer)

        page = urlopen(request, timeout=timeout)
        if not isinstance(page, basestring):
            page = decode_page(page)

        return page

    def _refresh_authentication_token(self):
        token_request_arguments = dict(
                username=self.username,
                password=self.password,
                referer=self.referer,
                expiration=self.requested_token_lifetime_minutes,
                f='json')

        url = _REQUEST_AUTHENTICATION_URL % urlencode(token_request_arguments)
        response = json.loads(self._fetch(url))

        if not 'token' in response:
            raise GeocoderAuthenticationFailure(
                'Missing token in auth request.'
                'Request URL: %s; response JSON: %s' %
                (url, json.dumps(response)))

        self.token = response['token']
        logger.debug('Got new auth token: %s' % self.token)
