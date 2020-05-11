import functools
import json
import warnings
from socket import timeout as SocketTimeout
from ssl import SSLError

from geopy.compat import (
    HTTPError,
    ProxyHandler,
    Request,
    URLError,
    build_opener_with_context,
    py3k,
    string_compare,
)
from geopy.exc import (
    ConfigurationError,
    GeocoderAuthenticationFailure,
    GeocoderInsufficientPrivileges,
    GeocoderParseError,
    GeocoderQueryError,
    GeocoderQuotaExceeded,
    GeocoderServiceError,
    GeocoderTimedOut,
    GeocoderUnavailable,
)
from geopy.point import Point
from geopy.util import __version__, decode_page, logger

__all__ = (
    "Geocoder",
    "options",
)

_DEFAULT_USER_AGENT = "geopy/%s" % __version__


class options(object):
    """The `options` object contains default configuration values for
    geocoders, e.g. `timeout` and `User-Agent`.
    Instead of passing a custom value to each geocoder individually, you can
    override a default value in this object.

    Please note that not all geocoders use all attributes of this object.
    For example, some geocoders don't respect the ``default_scheme``
    attribute. Refer to the specific geocoder's initializer doc for a list
    of parameters which that geocoder accepts.

    Example for overriding default ``timeout`` and ``user_agent``::

        >>> import geopy.geocoders
        >>> from geopy.geocoders import Nominatim
        >>> geopy.geocoders.options.default_user_agent = 'my_app/1'
        >>> geopy.geocoders.options.default_timeout = 7
        >>> geolocator = Nominatim()
        >>> print(geolocator.headers)
        {'User-Agent': 'my_app/1'}
        >>> print(geolocator.timeout)
        7

    Attributes:
        default_format_string
            String containing ``'%s'`` where the string to geocode should
            be interpolated before querying the geocoder. Used by `geocode`
            calls only. For example: ``'%s, Mountain View, CA'``.

            .. deprecated:: 1.22.0
                ``format_string`` is deprecated in favor of more advanced
                alternatives (see :ref:`Specifying Parameters Once
                <specifying_parameters_once>`) and will be removed in
                geopy 2.0.

        default_proxies
            Tunnel requests through HTTP proxy.

            By default the system proxies are respected (e.g.
            `HTTP_PROXY` and `HTTPS_PROXY` env vars or platform-specific
            proxy settings, such as macOS or Windows native
            preferences -- see :class:`urllib.request.ProxyHandler` for
            more details). The `proxies` value for using system proxies
            is ``None``.

            To disable system proxies and issue requests directly,
            explicitly pass an empty dict as a value for `proxies`: ``{}``.

            To use a custom HTTP proxy location, pass a string.
            Valid examples are:

            - ``"192.0.2.0:8080"``
            - ``"john:passw0rd@192.0.2.0:8080"``
            - ``"http://john:passw0rd@192.0.2.0:8080"``

            Please note:

            - Scheme part (``http://``) of the proxy is ignored.
            - Only `http` proxy is supported. Even if the proxy scheme
              is `https`, it will be ignored, and the connection between
              client and proxy would still be unencrypted.
              However, `https` requests via `http` proxy are still
              supported (via `HTTP CONNECT` method).


            Raw urllib-style `proxies` dict might be provided instead of
            a string:

            - ``{"https": "192.0.2.0:8080"}`` -- means that HTTP proxy
              would be used only for requests having `https` scheme.
              String `proxies` value is automatically used for both
              schemes, and is provided as a shorthand for the urllib-style
              `proxies` dict.

            For more information, see
            documentation on :class:`urllib.request.ProxyHandler`.

            .. versionchanged:: 1.15.0
               Added support for the string value.

        default_scheme
            Use ``'https'`` or ``'http'`` as the API URL's scheme.

        default_ssl_context
            An :class:`ssl.SSLContext` instance with custom TLS
            verification settings. Pass ``None`` to use the interpreter's
            defaults (starting from Python 2.7.9 and 3.4.3 that is to use
            the system's trusted CA certificates; the older versions don't
            support TLS verification completely).

            For older versions of Python (before 2.7.9 and 3.4.3) this
            argument is ignored, as `urlopen` doesn't accept an ssl
            context there, and a warning is issued.

            To use the CA bundle used by `requests` library::

                import ssl
                import certifi
                import geopy.geocoders
                ctx = ssl.create_default_context(cafile=certifi.where())
                geopy.geocoders.options.default_ssl_context = ctx

            To disable TLS certificate verification completely::

                import ssl
                import geopy.geocoders
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                geopy.geocoders.options.default_ssl_context = ctx

            See docs for the :class:`ssl.SSLContext` class for more examples.

        default_timeout
            Time, in seconds, to wait for the geocoding service to respond
            before raising a :class:`geopy.exc.GeocoderTimedOut` exception.
            Pass `None` to disable timeout.

            .. note::
               Currently ``None`` as a value is processed correctly only
               for the ``geopy.geocoders.options.default_timeout`` option
               value. ``timeout=None`` as a method argument (i.e.
               ``geocoder.geocode(..., timeout=None)``) would be treated
               as "use timeout, as set in
               ``geopy.geocoders.options.default_timeout``", and
               a deprecation warning would be raised.
               In geopy 2.0 this will change, so that ``timeout=None``
               would actually disable timeout.

        default_user_agent
            User-Agent header to send with the requests to geocoder API.
    """

    # Please keep the attributes sorted (Sphinx sorts them in the rendered
    # docs) and make sure that each attr has a corresponding section in
    # the docstring above.
    #
    # It's bad to have the attrs docs separated from the attrs
    # themselves. Although Sphinx supports docstrings for each attr [1],
    # this is not standardized and won't work with `help()` function and
    # in the ReadTheDocs (at least out of the box) [2].
    #
    # [1]: http://www.sphinx-doc.org/en/master/ext/autodoc.html#directive-autoattribute
    # [2]: https://github.com/rtfd/readthedocs.org/issues/855#issuecomment-261337038
    default_format_string = '%s'
    default_proxies = None
    default_scheme = 'https'
    default_ssl_context = None
    default_timeout = 1
    default_user_agent = _DEFAULT_USER_AGENT


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
    429: GeocoderQuotaExceeded,
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
        if format_string is not None or options.default_format_string != "%s":
            warnings.warn(
                '`format_string` is deprecated. Please pass the already '
                'formatted queries to `geocode` instead. See '
                '`Specifying Parameters Once` section in docs for more '
                'details. In geopy 2.0 `format_string` will be removed.',
                DeprecationWarning, stacklevel=3
            )
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

        if isinstance(self.proxies, string_compare):
            self.proxies = {'http': self.proxies, 'https': self.proxies}

        # `ProxyHandler` should be present even when actually there're
        # no proxies. `build_opener` contains it anyway. By specifying
        # it here explicitly we can disable system proxies (i.e.
        # from HTTP_PROXY env var) by setting `self.proxies` to `{}`.
        # Otherwise, if we didn't specify ProxyHandler for empty
        # `self.proxies` here, build_opener would have used one internally
        # which could have unwillingly picked up the system proxies.
        opener = build_opener_with_context(
            self.ssl_context,
            ProxyHandler(self.proxies),
        )
        self.urlopen = opener.open

    @staticmethod
    def _coerce_point_to_string(point, output_format="%(lat)s,%(lon)s"):
        """
        Do the right thing on "point" input. For geocoders with reverse
        methods.
        """
        try:
            if not isinstance(point, Point):
                point = Point(point)
        except ValueError as e:
            if isinstance(point, string_compare):
                warnings.warn(
                    'Unable to parse the string as Point: "%s". Using the value '
                    'as-is for the query. In geopy 2.0 this will become an '
                    'exception.' % str(e), DeprecationWarning, stacklevel=3
                )
                return point
            raise
        else:
            # Altitude is silently dropped.
            return output_format % dict(lat=point.latitude,
                                        lon=point.longitude)

    @staticmethod
    def _format_bounding_box(bbox, output_format="%(lat1)s,%(lon1)s,%(lat2)s,%(lon2)s"):
        """
        Transform bounding box boundaries to a string matching
        `output_format` from the following formats:

            - [Point(lat1, lon1), Point(lat2, lon2)]
            - [[lat1, lon1], [lat2, lon2]]
            - ["lat1,lon1", "lat2,lon2"]

        It is guaranteed that lat1 <= lat2 and lon1 <= lon2.
        """
        if len(bbox) != 2:
            raise GeocoderQueryError("Unsupported format for a bounding box")
        p1, p2 = bbox
        p1, p2 = Point(p1), Point(p2)
        return output_format % dict(lat1=min(p1.latitude, p2.latitude),
                                    lon1=min(p1.longitude, p2.longitude),
                                    lat2=max(p1.latitude, p2.latitude),
                                    lon2=max(p1.longitude, p2.longitude))

    def _geocoder_exception_handler(
            self, error, message, http_code=None, http_body=None
    ):
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
            req = url  # Don't construct an urllib's Request for a custom requester.

            # `requester` might be anything which can issue an HTTP request.
            # Assume that `requester` is a method of the `requests` library.
            # Requests, however, doesn't accept SSL context in its HTTP
            # request methods. A custom HTTP adapter has to be created for that.
            # So the current usage is not directly compatible with `requests`.
            requester = functools.partial(requester, context=self.ssl_context,
                                          proxies=self.proxies,
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
                 'default geocoder timeout. In geopy 2.0 the '
                 'behavior will be different: None will mean "no timeout" '
                 'instead of "default geocoder timeout". Pass '
                 'geopy.geocoders.base.DEFAULT_SENTINEL instead of None '
                 'to get rid of this warning.'), DeprecationWarning, stacklevel=3)
            timeout = DEFAULT_SENTINEL

        timeout = (timeout if timeout is not DEFAULT_SENTINEL
                   else self.timeout)

        try:
            page = requester(req, timeout=timeout, **kwargs)
        except Exception as error:
            message = (
                str(error) if not py3k
                else (
                    str(error.args[0])
                    if len(error.args)
                    else str(error)
                )
            )
            if isinstance(error, HTTPError):
                http_code = error.getcode()
                http_body = self._read_http_error_body(error)
                if http_body:
                    logger.info('Received an HTTP error (%s): %s', http_code, http_body,
                                exc_info=False)
            else:
                http_code = None
                http_body = None
            self._geocoder_exception_handler(error, message, http_code, http_body)
            if isinstance(error, HTTPError):
                try:
                    raise ERROR_CODE_MAP[http_code](message)
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

    def _read_http_error_body(self, error):
        try:
            return decode_page(error)
        except Exception:
            logger.debug('Unable to fetch body for a non-successful HTTP response',
                         exc_info=True)
            return None

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
