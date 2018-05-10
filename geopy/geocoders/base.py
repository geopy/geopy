"""
:class:`.GeoCoder` base object from which other geocoders are templated.
"""

from ssl import SSLError
from socket import timeout as SocketTimeout
import functools
import json
import warnings

from geopy.compat import (
    string_compare,
    HTTPError,
    py3k,
    build_opener_with_context,
    ProxyHandler,
    URLError,
    Request,
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
from geopy.util import decode_page, __version__


__all__ = (
    "Geocoder",
    "options",
)


class options(object):
    """The ``options`` object contains default configuration values for
    geocoders, e.g. timeout and User-Agent.
    Instead of passing a custom value to each geocoder individually, you can
    override a default value in this object.

    Please note that not all geocoders use all attributes of this object.
    For example, some geocoders don't respect the ``default_scheme``
    attribute. Refer to the specific geocoder's initializer doc for a list
    of parameters which that geocoder accepts.

    Example for overriding default ``timeout`` and ``user_agent``::

        >>> import geopy.geocoders
        >>> geopy.geocoders.options.default_user_agent = 'my_app/1'
        >>> geopy.geocoders.options.default_timeout = 7
        >>>
        >>> from geopy.geocoders import Nominatim
        >>> geolocator = Nominatim()
        >>> print(geolocator.headers)
        {'User-Agent': 'my_app/1'}
        >>> print(geolocator.timeout)
        7

    """

    default_format_string = '%s'
    """String containing ``'%s'`` where the string to geocode should be
    interpolated before querying the geocoder. Used by ``geocode`` calls only.
    For example: ``'%s, Mountain View, CA'``."""

    default_scheme = 'https'
    """Use ``'https'`` or ``'http'`` as the API URL's scheme."""

    default_timeout = 1
    """Time, in seconds, to wait for the geocoding service to respond before
    raising a :class:`geopy.exc.GeocoderTimedOut` exception. Pass ``None``
    to disable timeout."""

    default_proxies = None
    """If specified, tunnel requests through the specified proxy.
    E.g., ``{"https": "192.0.2.0"}``. For more information, see documentation
    on :class:`urllib2.ProxyHandler`."""

    default_user_agent = "geopy/%s" % __version__
    """User-Agent header to send with the requests to geocoder API."""

    default_ssl_context = None
    """An :class:`ssl.SSLContext` instance with custom TLS verification
    settings. Pass ``None`` to use the interpreter's defaults (starting from
    Python 2.7.9 and 3.4.3 that is to use the system's trusted CA certificates;
    the older versions don't support TLS verification completely).

    For older versions of Python (before 2.7.9 and 3.4.3) this argument is
    ignored, as ``urlopen`` doesn't accept an ssl context there, and a warning
    is issued.

    To disable TLS certificate verification completely::

        >>> import ssl
        >>> import geopy.geocoders
        >>> ctx = ssl.create_default_context()
        >>> ctx.check_hostname = False
        >>> ctx.verify_mode = ssl.CERT_NONE
        >>> geopy.geocoders.options.default_ssl_context = ctx

    See docs for the :class:`ssl.SSLContext` class for more examples.
    """


# Create an object which `repr` returns 'DEFAULT_SENTINEL'. Sphinx (docs) uses
# this value when generating method's signature.
DEFAULT_SENTINEL = type('object', (object,),
                        {'__repr__': lambda self: 'DEFAULT_SENTINEL'})()

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


class Geocoder(object):
    """
    Template object for geocoders.
    """

    def __init__(
            self,
            format_string=None,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """
        Mostly-common geocoder validation, proxies, &c. Not all geocoders
        specify format_string and such.
        """
        self.format_string = format_string or options.default_format_string
        self.scheme = scheme or options.default_scheme
        if self.scheme not in ('http', 'https'):
            raise ConfigurationError(
                'Supported schemes are `http` and `https`.'
            )
        self.timeout = (timeout if timeout is not DEFAULT_SENTINEL
                        else options.default_timeout)
        self.proxies = (proxies if proxies is not DEFAULT_SENTINEL
                        else options.default_proxies)
        self.headers = {'User-Agent': user_agent or options.default_user_agent}
        self.ssl_context = (ssl_context if ssl_context is not DEFAULT_SENTINEL
                            else options.default_ssl_context)

        if self.proxies:
            opener = build_opener_with_context(
                self.ssl_context,
                ProxyHandler(self.proxies),
            )
        else:
            opener = build_opener_with_context(
                self.ssl_context,
            )
        self.urlopen = opener.open

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

    def _geocoder_exception_handler(self, error, message):
        """
        Geocoder-specific exceptions handler.
        Override if custom exceptions processing is needed.
        For example, raising an appropriate GeocoderQuotaExceeded on non-200
        response with a textual message in the body about the exceeded quota.
        """
        pass

    def _call_geocoder(
            self,
            url,
            timeout=DEFAULT_SENTINEL,
            raw=False,
            requester=None,
            deserializer=json.loads,
            **kwargs
    ):
        """
        For a generated query URL, get the results.
        """

        if requester:
            req = url  # Don't construct an urllib's Request for a custom requester
            requester = functools.partial(requester, context=self.ssl_context,
                                          headers=self.headers)
        else:
            if isinstance(url, Request):
                # copy Request
                headers = self.headers.copy()
                headers.update(url.header_items())
                req = Request(url=url.get_full_url(), headers=headers)
            else:
                req = Request(url=url, headers=self.headers)

        requester = requester or self.urlopen

        if timeout is None:
            warnings.warn(
                ('`timeout=None` has been passed to a geocoder call. Using '
                 'default geocoder timeout. In future versions of geopy the '
                 'behavior will be different: None will mean "no timeout" '
                 'instead of "default geocoder timeout".'), DeprecationWarning)
            timeout = DEFAULT_SENTINEL

        timeout = (timeout if timeout is not DEFAULT_SENTINEL
                   else self.timeout)

        try:
            page = requester(req, timeout=timeout, **kwargs)
        except Exception as error: # pylint: disable=W0703
            message = (
                str(error) if not py3k
                else (
                    str(error.args[0])
                    if len(error.args)
                    else str(error)
                )
            )
            self._geocoder_exception_handler(error, message)
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

        if deserializer is not None:
            try:
                return deserializer(page)
            except ValueError:
                raise GeocoderParseError(
                    "Could not deserialize using deserializer:\n%s" % page
                )
        else:
            return page

    def geocode(self, query, exactly_one=True, timeout=DEFAULT_SENTINEL):
        """
        Implemented in subclasses.
        """
        raise NotImplementedError()

    def reverse(self, query, exactly_one=True, timeout=DEFAULT_SENTINEL):
        """
        Implemented in subclasses.
        """
        raise NotImplementedError()
