"""
:class:`.GeoCoder` base object from which other geocoders are templated.
"""

from ssl import SSLError
from socket import timeout as SocketTimeout
import json

from geopy.compat import (
    string_compare,
    HTTPError,
    py3k,
    urlopen as urllib_urlopen,
    build_opener,
    ProxyHandler,
    URLError,
    install_opener,
)
from geopy.point import Point
from geopy.exc import (
    GeocoderServiceError,
    ConfigurationError,
    GeocoderTimedOut,
    GeocoderAuthenticationFailure,
    GeocoderQuotaExceeded,
    GeocoderQueryError,
    GeocoderInsufficientPrivileges,
    GeocoderUnavailable,
    GeocoderParseError,
)
from geopy.util import decode_page


__all__ = (
    "Geocoder",
    "DEFAULT_FORMAT_STRING",
    "DEFAULT_SCHEME",
    "DEFAULT_TIMEOUT",
    "DEFAULT_WKID",
)


DEFAULT_FORMAT_STRING = '%s'
DEFAULT_SCHEME = 'https'
DEFAULT_TIMEOUT = 1
DEFAULT_WKID = 4326

ERROR_CODE_MAP = {
    400: GeocoderQueryError,
    401: GeocoderAuthenticationFailure,
    402: GeocoderQuotaExceeded,
    403: GeocoderInsufficientPrivileges,
    407: GeocoderAuthenticationFailure,
    412: GeocoderQueryError,
    413: GeocoderQueryError,
    414: GeocoderQueryError,
    502: GeocoderServiceError,
    503: GeocoderTimedOut,
    504: GeocoderTimedOut
}


class Geocoder(object): # pylint: disable=R0921
    """
    Template object for geocoders.
    """

    def __init__(
            self,
            format_string=DEFAULT_FORMAT_STRING,
            scheme=DEFAULT_SCHEME,
            timeout=DEFAULT_TIMEOUT,
            proxies=None
        ):
        """
        Mostly-common geocoder validation, proxies, &c. Not all geocoders
        specify format_string and such.
        """
        self.format_string = format_string
        self.scheme = scheme
        if self.scheme not in ('http', 'https'): # pragma: no cover
            raise ConfigurationError(
                'Supported schemes are `http` and `https`.'
            )
        self.proxies = proxies
        self.timeout = timeout

        if self.proxies:
            install_opener(
                build_opener(
                    ProxyHandler(self.proxies)
                )
            )
        self.urlopen = urllib_urlopen

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

    def _call_geocoder(
            self,
            url,
            timeout=None,
            raw=False,
            requester=None,
            **kwargs
        ):
        """
        For a generated query URL, get the results.
        """
        requester = requester or self.urlopen

        try:
            page = requester(url, timeout=(timeout or self.timeout), **kwargs)
        except Exception as error: # pylint: disable=W0703
            message = (
                str(error) if not py3k
                else (
                    str(error.args[0])
                    if len(error.args)
                    else str(error)
                )
            )
            if hasattr(self, '_geocoder_exception_handler'):
                self._geocoder_exception_handler(error, message) # pylint: disable=E1101
            if isinstance(error, HTTPError):
                code = error.getcode()
                try:
                    raise ERROR_CODE_MAP[code](message)
                except KeyError:
                    raise GeocoderServiceError(message)
            elif isinstance(error, URLError):
                if "timed out" in message:
                    raise GeocoderTimedOut('Service timed out')
                elif "unreachable" in message:
                    raise GeocoderUnavailable('Service not available')
            elif isinstance(error, SocketTimeout):
                raise GeocoderTimedOut('Service timed out')
            elif isinstance(error, SSLError):
                if "timed out" in message:
                    raise GeocoderTimedOut('Service timed out')
            raise GeocoderServiceError(message)

        if hasattr(page, 'getcode'):
            status_code = page.getcode()
        elif hasattr(page, 'status_code'):
            status_code = page.status_code
        else:
            status_code = None
        if status_code in ERROR_CODE_MAP:
            raise ERROR_CODE_MAP[page.status_code]("\n%s" % decode_page(page))

        if raw:
            return page

        page = decode_page(page)
        try:
            return json.loads(page)
        except ValueError:
            raise GeocoderParseError(
                "Could not deserialize from JSON:\n%s" % page
            )

    def geocode(self, query, exactly_one=True, timeout=None):
        """
        Implemented in subclasses.
        """
        raise NotImplementedError()

    def reverse(self, query, exactly_one=True, timeout=None):
        """
        Implemented in subclasses.
        """
        raise NotImplementedError()
