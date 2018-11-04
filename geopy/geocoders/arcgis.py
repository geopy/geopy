import json
import warnings
from time import time

from geopy.compat import Request, string_compare, urlencode
from geopy.exc import (
    ConfigurationError,
    GeocoderAuthenticationFailure,
    GeocoderServiceError,
)
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("ArcGIS", )

DEFAULT_WKID = 4326


class ArcGIS(Geocoder):
    """Geocoder using the ERSI ArcGIS API.

    Documentation at:
        https://developers.arcgis.com/rest/geocode/api-reference/overview-world-geocoding-service.htm
    """

    _TOKEN_EXPIRED = 498
    _MAX_RETRIES = 3

    auth_path = '/sharing/generateToken'
    geocode_path = '/arcgis/rest/services/World/GeocodeServer/findAddressCandidates'
    reverse_path = '/arcgis/rest/services/World/GeocodeServer/reverseGeocode'

    def __init__(
            self,
            username=None,
            password=None,
            referer=None,
            token_lifetime=60,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            format_string=None,
            ssl_context=DEFAULT_SENTINEL,
            auth_domain='www.arcgis.com',
            domain='geocode.arcgis.com',
    ):
        """

        :param str username: ArcGIS username. Required if authenticated
            mode is desired.

        :param str password: ArcGIS password. Required if authenticated
            mode is desired.

        :param str referer: Required if authenticated mode is desired.
            `Referer` HTTP header to send with each request,
            e.g., ``'http://www.example.com'``. This is tied to an issued token,
            so fielding queries for multiple referrers should be handled by
            having multiple ArcGIS geocoder instances.

        :param int token_lifetime: Desired lifetime, in minutes, of an
            ArcGIS-issued token.

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`.
            If authenticated mode is in use, it must be ``'https'``.

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

        :param str auth_domain: Domain where the target ArcGIS auth service
            is hosted. Used only in authenticated mode (i.e. username,
            password and referer are set).

            .. versionadded:: 1.17.0

        :param str domain: Domain where the target ArcGIS service
            is hosted.

            .. versionadded:: 1.17.0
        """
        super(ArcGIS, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
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
        self.auth_domain = auth_domain.strip('/')
        self.auth_api = (
            '%s://%s%s' % (self.scheme, self.auth_domain, self.auth_path)
        )

        self.token = None
        self.token_lifetime = token_lifetime * 60  # store in seconds
        self.token_expiry = None
        self.retry = 1

        self.domain = domain.strip('/')
        self.api = (
            '%s://%s%s' % (self.scheme, self.domain, self.geocode_path)
        )
        self.reverse_api = (
            '%s://%s%s' % (self.scheme, self.domain, self.reverse_path)
        )

    def _authenticated_call_geocoder(self, url, timeout=DEFAULT_SENTINEL):
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

    def geocode(self, query, exactly_one=True, timeout=DEFAULT_SENTINEL,
                out_fields=None):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param out_fields: A list of output fields to be returned in the
            attributes field of the raw data. This can be either a python
            list/tuple of fields or a comma-separated string. See
            https://developers.arcgis.com/rest/geocode/api-reference/geocoding-service-output.htm
            for a list of supported output fields. If you want to return all
            supported output fields, set ``out_fields="*"``.

            .. versionadded:: 1.14.0
        :type out_fields: str or iterable

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = {'singleLine': self.format_string % query, 'f': 'json'}
        if exactly_one:
            params['maxLocations'] = 1
        if out_fields is not None:
            if isinstance(out_fields, string_compare):
                params['outFields'] = out_fields
            else:
                params['outFields'] = ",".join(out_fields)
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
        if not len(response['candidates']):
            return None
        geocoded = []
        for resource in response['candidates']:
            geometry = resource['location']
            geocoded.append(
                Location(
                    resource['address'], (geometry['y'], geometry['x']), resource
                )
            )
        if exactly_one:
            return geocoded[0]
        return geocoded

    def reverse(self, query, exactly_one=True, timeout=DEFAULT_SENTINEL,
                distance=None, wkid=DEFAULT_WKID):
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

        :param int distance: Distance from the query location, in meters,
            within which to search. ArcGIS has a default of 100 meters, if not
            specified.

        :param str wkid: WKID to use for both input and output coordinates.

            .. deprecated:: 1.14.0
               It wasn't working before because it was specified incorrectly
               in the request parameters, and won't work even if we fix the
               request, because :class:`geopy.point.Point` normalizes the
               coordinates according to WKID 4326. Please open an issue in
               the geopy issue tracker if you believe that custom wkid values
               should be supported.
               This parameter is scheduled for removal in geopy 2.0.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        location = self._coerce_point_to_string(query, "%(lon)s,%(lat)s")
        if wkid != DEFAULT_WKID:
            warnings.warn("%s.reverse: custom wkid value has been ignored.  "
                          "It wasn't working before because it was specified "
                          "incorrectly in the request parameters, and won't "
                          "work even if we fix the request, because geopy.Point "
                          "normalizes the coordinates according to WKID %s. "
                          "Please open an issue in the geopy issue tracker "
                          "if you believe that custom wkid values should be "
                          "supported." % (type(self).__name__, DEFAULT_WKID),
                          DeprecationWarning, stacklevel=2)
            wkid = DEFAULT_WKID
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
            # https://developers.arcgis.com/rest/geocode/api-reference/geocoding-service-output.htm
            if response['error']['code'] == 400:
                # 'details': ['Unable to find address for the specified location.']}
                try:
                    if 'Unable to find' in response['error']['details'][0]:
                        return None
                except (KeyError, IndexError):
                    pass
            raise GeocoderServiceError(str(response['error']))
        address = (
            "%(Address)s, %(City)s, %(Region)s %(Postal)s,"
            " %(CountryCode)s" % response['address']
        )
        location = Location(
            address,
            (response['location']['y'], response['location']['x']),
            response['address']
        )
        if exactly_one:
            return location
        else:
            return [location]

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
