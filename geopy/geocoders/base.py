"""
:class:`.GeoCoder` base object from which other geocoders are templated.
"""

try:
    from urllib2 import (urlopen as urllib_urlopen, build_opener,
        ProxyHandler, URLError)
except ImportError: # pragma: no cover
    from urllib.request import (urlopen as urllib_urlopen, # pylint: disable=F0401,E0611
        build_opener, ProxyHandler, URLError)
from ssl import SSLError
from socket import timeout as SocketTimeout
import json

from geopy.compat import string_compare, HTTPError
from geopy.point import Point
from geopy.exc import (GeocoderServiceError, ConfigurationError,
    GeocoderTimedOut, GeocoderAuthenticationFailure)
from geopy.util import decode_page

DEFAULT_FORMAT_STRING = '%s'
DEFAULT_SCHEME = 'https'
DEFAULT_TIMEOUT = 1


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
            if hasattr(self, '_geocoder_exception_handler'):
                self._geocoder_exception_handler(error) # pylint: disable=E1101
            if isinstance(error, HTTPError):
                if error.msg.lower().contains("unauthorized"):
                    raise GeocoderAuthenticationFailure("Unauthorized")
                raise GeocoderServiceError(error.getcode(), error.msg)
            elif isinstance(error, URLError):
                if error.message == '<urlopen error timed out>':
                    raise GeocoderTimedOut('Service timed out')
                raise
            elif isinstance(error, SocketTimeout):
                raise GeocoderTimedOut('Service timed out')
            elif isinstance(error, SSLError):
                if error.message == 'The read operation timed out':
                    raise GeocoderTimedOut('Service timed out')
                raise
            else:
                raise
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
