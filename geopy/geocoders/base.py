"""
:class:`.GeoCoder` base object from which other geocoders are templated.
"""

from ssl import SSLError
from socket import timeout as SocketTimeout
import json

from geopy.compat import string_compare, HTTPError, py3k, \
    urlopen as urllib_urlopen, build_opener, ProxyHandler, URLError
from geopy.point import Point
from geopy.exc import (GeocoderServiceError, ConfigurationError,
    GeocoderTimedOut, GeocoderAuthenticationFailure, GeocoderQuotaExceeded,
    GeocoderQueryError, GeocoderInsufficientPrivileges)
from geopy.util import decode_page

DEFAULT_FORMAT_STRING = '%s'
DEFAULT_SCHEME = 'https'
DEFAULT_TIMEOUT = 1
DEFAULT_WKID = 4326


class Geocoder(object): # pylint: disable=R0921
    """
    Template object for geocoders.
    """

    def __init__(self, format_string=DEFAULT_FORMAT_STRING, scheme=DEFAULT_SCHEME,
                        timeout=DEFAULT_TIMEOUT, proxies=None):
        """
        Mostly-common geocoder validation, proxies, &c. Not all geocoders
        specify format_string and such.
        """
        self.format_string = format_string
        self.scheme = scheme
        if self.scheme not in ('http', 'https'): # pragma: no cover
            raise ConfigurationError('Supported schemes are `http` and `https`.')
        self.proxies = proxies
        self.timeout = timeout

        # Add urllib proxy support using environment variables or
        # built in OS proxy details
        # See: http://docs.python.org/2/library/urllib2.html
        # And: http://stackoverflow.com/questions/1450132/proxy-with-urllib2
        if self.proxies is None:
            self.urlopen = urllib_urlopen
        else:
            self.urlopen = build_opener(
                ProxyHandler(self.proxies)
            )

    @staticmethod
    def _coerce_point_to_string(point):
        """
        Do the right thing on "point" input. For geocoders with reverse
        methods.
        """
        if isinstance(point, Point):
            return ",".join((str(point.latitude), str(point.longitude)))
        elif isinstance(point, (list, tuple)):
            return ",".join((str(point[0]), str(point[1]))) # -altitude
        elif isinstance(point, string_compare):
            return point
        else: # pragma: no cover
            raise ValueError("Invalid point")

    def _parse_json(self, page, exactly_one): # pragma: no cover
        """
        Template for subclasses
        """
        raise NotImplementedError()

    def _call_geocoder(self, url, timeout=None, raw=False):
        """
        For a generated query URL, get the results.
        """
        try:
            page = self.urlopen(url, timeout=timeout or self.timeout)
        except Exception as error: # pylint: disable=W0703
            message = str(error) if not py3k else \
                        (str(error.args[0] if len(error.args) else str(error)))
            if hasattr(self, '_geocoder_exception_handler'):
                self._geocoder_exception_handler(error, message) # pylint: disable=E1101
            if isinstance(error, HTTPError):
                code = error.getcode()
                error_code_map = {
                    400: GeocoderQueryError,
                    401: GeocoderAuthenticationFailure,
                    402: GeocoderQuotaExceeded,
                    403: GeocoderInsufficientPrivileges,
                    408: GeocoderTimedOut,
                    409: GeocoderAuthenticationFailure,
                    502: GeocoderServiceError,
                    503: GeocoderTimedOut,
                    504: GeocoderTimedOut
                }
                try:
                    raise error_code_map[code](message)
                except KeyError:
                    raise GeocoderServiceError(message)
            elif isinstance(error, URLError):
                if "timed out" in message:
                    raise GeocoderTimedOut('Service timed out')
            elif isinstance(error, SocketTimeout):
                raise GeocoderTimedOut('Service timed out')
            elif isinstance(error, SSLError):
                if "timed out in message":
                    raise GeocoderTimedOut('Service timed out')
            if not py3k:
                err = GeocoderServiceError(message)
                err.__traceback__ = error
                raise err
            else:
                raise GeocoderServiceError(message)
        if raw:
            return page
        return json.loads(decode_page(page))

    def geocode(self, query, exactly_one=True, timeout=None): # pylint: disable=R0201,W0613
        """
        Implemented in subclasses.
        """
        raise NotImplementedError()

    def reverse(self, query, exactly_one=True, timeout=None): # pragma: no cover
        """
        Implemented in subclasses.
        """
        raise NotImplementedError()
