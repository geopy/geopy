import asyncio
import functools
import inspect
import threading

from geopy import compat
from geopy.adapters import (
    AdapterHTTPError,
    BaseAsyncAdapter,
    BaseSyncAdapter,
    RequestsAdapter,
    URLLibAdapter,
    get_retry_after,
)
from geopy.exc import (
    ConfigurationError,
    GeocoderAuthenticationFailure,
    GeocoderInsufficientPrivileges,
    GeocoderQueryError,
    GeocoderQuotaExceeded,
    GeocoderRateLimited,
    GeocoderServiceError,
    GeocoderTimedOut,
)
from geopy.point import Point
from geopy.util import __version__, logger

__all__ = (
    "Geocoder",
    "options",
)

_DEFAULT_USER_AGENT = "geopy/%s" % __version__

_DEFAULT_ADAPTER_CLASS = next(
    adapter_cls
    for adapter_cls in (RequestsAdapter, URLLibAdapter,)
    if adapter_cls.is_available
)


class options:
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
        default_adapter_factory
            A callable which returns a :class:`geopy.adapters.BaseAdapter`
            instance. Adapters are different implementations of HTTP clients.
            See :mod:`geopy.adapters` for more info.

            This callable accepts two keyword args: ``proxies`` and ``ssl_context``.
            A class might be specified as this callable as well.

            Example::

                import geopy.geocoders
                geopy.geocoders.options.default_adapter_factory \
= geopy.adapters.URLLibAdapter

                geopy.geocoders.options.default_adapter_factory = (
                    lambda proxies, ssl_context: MyAdapter(
                        proxies=proxies, ssl_context=ssl_context, my_custom_arg=42
                    )
                )

            If `requests <https://requests.readthedocs.io>`_ package is
            installed, the default adapter is
            :class:`geopy.adapters.RequestsAdapter`. Otherwise it is
            :class:`geopy.adapters.URLLibAdapter`.

            .. versionadded:: 2.0

        default_proxies
            Tunnel requests through HTTP proxy.

            By default the system proxies are respected (e.g.
            `HTTP_PROXY` and `HTTPS_PROXY` env vars or platform-specific
            proxy settings, such as macOS or Windows native
            preferences -- see :func:`urllib.request.getproxies` for
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
            documentation on :func:`urllib.request.getproxies`.

        default_scheme
            Use ``'https'`` or ``'http'`` as the API URL's scheme.

        default_ssl_context
            An :class:`ssl.SSLContext` instance with custom TLS
            verification settings. Pass ``None`` to use the interpreter's
            defaults (that is to use the system's trusted CA certificates).

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
    default_adapter_factory = _DEFAULT_ADAPTER_CLASS
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
    408: GeocoderTimedOut,
    412: GeocoderQueryError,
    413: GeocoderQueryError,
    414: GeocoderQueryError,
    429: GeocoderRateLimited,
    502: GeocoderServiceError,
    503: GeocoderTimedOut,
    504: GeocoderTimedOut
}

NONE_RESULT = object()  # special return value for `_geocoder_exception_handler`


class Geocoder:
    """
    Template object for geocoders.
    """

    def __init__(
            self,
            *,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
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

        if isinstance(self.proxies, str):
            self.proxies = {'http': self.proxies, 'https': self.proxies}

        if adapter_factory is None:
            adapter_factory = options.default_adapter_factory
        self.adapter = adapter_factory(
            proxies=self.proxies,
            ssl_context=self.ssl_context,
        )
        if isinstance(self.adapter, BaseSyncAdapter):
            self.__run_async = False
        elif isinstance(self.adapter, BaseAsyncAdapter):
            self.__run_async = True
        else:
            raise ConfigurationError(
                "Adapter %r must extend either BaseSyncAdapter or BaseAsyncAdapter"
                % (type(self.adapter),)
            )

    def __enter__(self):
        """Context manager for synchronous adapters. At exit all
        open connections will be closed.

        In synchronous mode context manager usage is not required,
        and connections will be automatically closed by garbage collection.
        """
        if self.__run_async:
            raise TypeError("`async with` must be used with async adapters")
        res = self.adapter.__enter__()
        assert res is self.adapter, "adapter's __enter__ must return `self`"
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.adapter.__exit__(exc_type, exc_val, exc_tb)

    async def __aenter__(self):
        """Context manager for asynchronous adapters. At exit all
        open connections will be closed.

        In asynchronous mode context manager usage is not required,
        however, it is strongly advised to avoid warnings about
        resources leaks.
        """
        if not self.__run_async:
            raise TypeError("`async with` cannot be used with sync adapters")
        res = await self.adapter.__aenter__()
        assert res is self.adapter, "adapter's __enter__ must return `self`"
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.adapter.__aexit__(exc_type, exc_val, exc_tb)

    def _coerce_point_to_string(self, point, output_format="%(lat)s,%(lon)s"):
        """
        Do the right thing on "point" input. For geocoders with reverse
        methods.
        """
        if not isinstance(point, Point):
            point = Point(point)

        # Altitude is silently dropped.
        #
        # Geocoding services (almost?) always consider only lat and lon
        # in queries, so altitude doesn't affect the request.
        # A non-zero altitude should not raise an exception
        # though, because PoIs are assumed to span the whole
        # altitude axis (i.e. not just the 0km plane).
        return output_format % dict(lat=point.latitude,
                                    lon=point.longitude)

    def _format_bounding_box(
        self, bbox, output_format="%(lat1)s,%(lon1)s,%(lat2)s,%(lon2)s"
    ):
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

    def _geocoder_exception_handler(self, error):
        """
        Geocoder-specific exceptions handler.
        Override if custom exceptions processing is needed.
        For example, raising an appropriate GeocoderQuotaExceeded on non-200
        response with a textual message in the body about the exceeded quota.

        Return `NONE_RESULT` to have the geocoding call return `None` (meaning
        empty result).
        """
        pass

    def _call_geocoder(
            self,
            url,
            callback,
            *,
            timeout=DEFAULT_SENTINEL,
            is_json=True,
            headers=None
    ):
        """
        For a generated query URL, get the results.
        """

        req_headers = self.headers.copy()
        if headers:
            req_headers.update(headers)

        timeout = (timeout if timeout is not DEFAULT_SENTINEL
                   else self.timeout)

        try:
            if is_json:
                result = self.adapter.get_json(url, timeout=timeout, headers=req_headers)
            else:
                result = self.adapter.get_text(url, timeout=timeout, headers=req_headers)
            if self.__run_async:
                async def fut():
                    try:
                        res = callback(await result)
                        if inspect.isawaitable(res):
                            res = await res
                        return res
                    except Exception as error:
                        res = self._adapter_error_handler(error)
                        if res is NONE_RESULT:
                            return None
                        raise

                return fut()
            else:
                return callback(result)
        except Exception as error:
            res = self._adapter_error_handler(error)
            if res is NONE_RESULT:
                return None
            raise

    def _adapter_error_handler(self, error):
        if isinstance(error, AdapterHTTPError):
            if error.text:
                logger.info(
                    'Received an HTTP error (%s): %s',
                    error.status_code,
                    error.text,
                    exc_info=False,
                )
            res = self._geocoder_exception_handler(error)
            if res is NONE_RESULT:
                return NONE_RESULT
            exc_cls = ERROR_CODE_MAP.get(error.status_code, GeocoderServiceError)
            if issubclass(exc_cls, GeocoderRateLimited):
                raise exc_cls(
                    str(error), retry_after=get_retry_after(error.headers)
                ) from error
            else:
                raise exc_cls(str(error)) from error
        else:
            res = self._geocoder_exception_handler(error)
            if res is NONE_RESULT:
                return NONE_RESULT

    # def geocode(self, query, *, exactly_one=True, timeout=DEFAULT_SENTINEL):
    #     raise NotImplementedError()

    # def reverse(self, query, *, exactly_one=True, timeout=DEFAULT_SENTINEL):
    #     raise NotImplementedError()


def _synchronized(func):
    """A decorator for geocoder methods which makes the method always run
    under a lock. The lock is reentrant.

    This decorator transparently handles sync and async working modes.
    """

    sync_lock = threading.RLock()

    def locked_sync(self, *args, **kwargs):
        with sync_lock:
            return func(self, *args, **kwargs)

    # At the moment this decorator is evaluated we don't know if we
    # will work in sync or async mode.
    # But we shouldn't create the asyncio Lock in sync mode to avoid
    # unwanted implicit loop initialization.
    async_lock = None  # asyncio.Lock()
    async_lock_task = None  # support reentrance

    async def locked_async(self, *args, **kwargs):
        nonlocal async_lock
        nonlocal async_lock_task

        if async_lock is None:
            async_lock = asyncio.Lock()

        if async_lock.locked():
            assert async_lock_task is not None
            if compat.current_task() is async_lock_task:
                res = func(self, *args, **kwargs)
                if inspect.isawaitable(res):
                    res = await res
                return res

        async with async_lock:
            async_lock_task = compat.current_task()
            try:
                res = func(self, *args, **kwargs)
                if inspect.isawaitable(res):
                    res = await res
                return res
            finally:
                async_lock_task = None

    @functools.wraps(func)
    def f(self, *args, **kwargs):
        run_async = isinstance(self.adapter, BaseAsyncAdapter)
        if run_async:
            return locked_async(self, *args, **kwargs)
        else:
            return locked_sync(self, *args, **kwargs)

    return f
