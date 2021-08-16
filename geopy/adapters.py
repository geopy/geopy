"""
Adapters are HTTP client implementations used by geocoders.

Some adapters might support keep-alives, request retries, http2,
persistence of Cookies, response compression and so on.

Adapters should be considered an implementation detail. Most of the time
you wouldn't need to know about their existence unless you want to tune
HTTP client settings.

.. versionadded:: 2.0
   Adapters are currently provided on a `provisional basis`_.

    .. _provisional basis: https://docs.python.org/3/glossary.html#term-provisional-api
"""
import abc
import asyncio
import contextlib
import email
import json
import time
import warnings
from socket import timeout as SocketTimeout
from ssl import SSLError
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import (
    HTTPSHandler,
    ProxyHandler,
    Request,
    URLError,
    build_opener,
    getproxies,
)

from geopy.exc import (
    GeocoderParseError,
    GeocoderServiceError,
    GeocoderTimedOut,
    GeocoderUnavailable,
    GeopyError,
)
from geopy.util import logger

try:
    import requests
    from requests.adapters import HTTPAdapter as RequestsHTTPAdapter

    requests_available = True
except ImportError:
    RequestsHTTPAdapter = object
    requests_available = False

try:
    import aiohttp
    import aiohttp.client_exceptions
    import yarl

    aiohttp_available = True
except ImportError:
    aiohttp_available = False


class AdapterHTTPError(IOError):
    """An exception which must be raised by adapters when an HTTP response
    with a non-successful status code has been received.

    Base Geocoder class translates this exception to an instance of
    :class:`geopy.exc.GeocoderServiceError`.

    """

    def __init__(self, message, *, status_code, headers, text):
        """

        :param str message: Standard exception message.
        :param int status_code: HTTP status code.
        :param dict headers: HTTP response readers. A mapping object
            with lowercased or case-insensitive keys.

            .. versionadded:: 2.2
        :param str text: HTTP body text.
        """
        self.status_code = status_code
        self.headers = headers
        self.text = text
        super().__init__(message)


def get_retry_after(headers):
    """Return Retry-After header value in seconds.

    .. versionadded:: 2.2
    """
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Retry-After
    # https://github.com/urllib3/urllib3/blob/1.26.4/src/urllib3/util/retry.py#L376

    try:
        retry_after = headers['retry-after']
    except KeyError:
        return None

    if not retry_after:  # None, ''
        return None

    retry_after = retry_after.strip()

    # RFC7231 section-7.1.3:
    # Retry-After = HTTP-date / delay-seconds

    try:
        # Retry-After: 120
        seconds = int(retry_after)
    except ValueError:
        # Retry-After: Fri, 31 Dec 1999 23:59:59 GMT
        retry_date_tuple = email.utils.parsedate_tz(retry_after)
        if retry_date_tuple is None:
            logger.warning('Invalid Retry-After header: %s', retry_after)
            return None
        retry_date = email.utils.mktime_tz(retry_date_tuple)
        seconds = retry_date - time.time()

    if seconds < 0:
        seconds = 0

    return seconds


class BaseAdapter(abc.ABC):
    """Base class for an Adapter.

    There are two types of adapters:

    - :class:`.BaseSyncAdapter` -- synchronous adapter,
    - :class:`.BaseAsyncAdapter` -- asynchronous (asyncio) adapter.

    Concrete adapter implementations must extend one of the two
    base adapters above.

    See :attr:`geopy.geocoders.options.default_adapter_factory`
    for details on how to specify an adapter to be used by geocoders.

    """

    # A class attribute which tells if this Adapter's required dependencies
    # are installed. By default assume that all Adapters are available.
    is_available = True

    def __init__(self, *, proxies, ssl_context):
        """Initialize adapter.

        :param dict proxies: An urllib-style proxies dict, e.g.
            ``{"http": "192.0.2.0:8080", "https": "192.0.2.0:8080"}``,
            ``{"https": "http://user:passw0rd@192.0.2.0:8080""}``.
            See :attr:`geopy.geocoders.options.default_proxies` (note
            that Adapters always receive a dict: the string proxy
            is transformed to dict in the base
            :class:`geopy.geocoders.base.Geocoder` class.).

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.

        """

    @abc.abstractmethod
    def get_json(self, url, *, timeout, headers):
        """Same as ``get_text`` except that the response is expected
        to be a valid JSON. The value returned is the parsed JSON.

        :class:`geopy.exc.GeocoderParseError` must be raised if
        the response cannot be parsed.

        :param str url: The target URL.

        :param float timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict headers: A dict with custom HTTP request headers.
        """

    @abc.abstractmethod
    def get_text(self, url, *, timeout, headers):
        """Make a GET request and return the response as string.

        This method should not raise any exceptions other than these:

        - :class:`geopy.adapters.AdapterHTTPError` should be raised if the response
          was successfully retrieved but the status code was non-successful.
        - :class:`geopy.exc.GeocoderTimedOut` should be raised when the request
          times out.
        - :class:`geopy.exc.GeocoderUnavailable` should be raised when the target
          host is unreachable.
        - :class:`geopy.exc.GeocoderServiceError` is the least specific error
          in the exceptions hierarchy and should be raised in any other cases.

        :param str url: The target URL.

        :param float timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict headers: A dict with custom HTTP request headers.
        """


class BaseSyncAdapter(BaseAdapter):
    """Base class for synchronous adapters.
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class BaseAsyncAdapter(BaseAdapter):
    """Base class for asynchronous adapters.

    See also: :ref:`Async Mode <async_mode>`.
    """

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def _normalize_proxies(proxies):
    """Normalize user-supplied `proxies`:

    - For `None` -- retrieve System proxies using
      :func:`urllib.request.getproxies`
    - Add `http://` scheme to proxy urls if missing.
    """
    if proxies is None:  # Use system proxy settings
        proxies = getproxies()
    if not proxies:
        return {}  # Disable proxies

    normalized = {}
    for scheme, url in proxies.items():
        if url and "://" not in url:
            # Without the scheme there are errors:
            # from aiohttp:
            #   ValueError: Only http proxies are supported
            # from requests (in some envs):
            #   urllib3.exceptions.ProxySchemeUnknown: Not supported
            #   proxy scheme localhost
            url = "http://%s" % url
        normalized[scheme] = url
    return normalized


class URLLibAdapter(BaseSyncAdapter):
    """The fallback adapter which uses urllib from the Python standard
    library, see :func:`urllib.request.urlopen`.

    urllib doesn't support keep-alives, request retries,
    doesn't persist Cookies and is HTTP/1.1 only.

    urllib was the only available option
    for making requests in geopy 1.x, so this adapter behaves the same
    as geopy 1.x in terms of HTTP requests.
    """

    def __init__(self, *, proxies, ssl_context):
        proxies = _normalize_proxies(proxies)
        super().__init__(proxies=proxies, ssl_context=ssl_context)

        # `ProxyHandler` should be present even when actually there're
        # no proxies. `build_opener` contains it anyway. By specifying
        # it here explicitly we can disable system proxies (i.e.
        # from HTTP_PROXY env var) by setting `proxies` to `{}`.
        # Otherwise, if we didn't specify ProxyHandler for empty
        # `proxies` here, the `build_opener` would have used one internally
        # which could have unwillingly picked up the system proxies.
        opener = build_opener(
            HTTPSHandler(context=ssl_context),
            ProxyHandler(proxies),
        )
        self.urlopen = opener.open

    def get_json(self, url, *, timeout, headers):
        text = self.get_text(url, timeout=timeout, headers=headers)
        try:
            return json.loads(text)
        except ValueError:
            raise GeocoderParseError(
                "Could not deserialize using deserializer:\n%s" % text
            )

    def get_text(self, url, *, timeout, headers):
        req = Request(url=url, headers=headers)
        try:
            page = self.urlopen(req, timeout=timeout)
        except Exception as error:
            message = str(error.args[0]) if len(error.args) else str(error)
            if isinstance(error, HTTPError):
                code = error.getcode()
                response_headers = {
                    name.lower(): value
                    for name, value in error.headers.items()
                }
                body = self._read_http_error_body(error)
                raise AdapterHTTPError(
                    message,
                    status_code=code,
                    headers=response_headers,
                    text=body,
                )
            elif isinstance(error, URLError):
                if "timed out" in message:
                    raise GeocoderTimedOut("Service timed out")
                elif "unreachable" in message:
                    raise GeocoderUnavailable("Service not available")
            elif isinstance(error, SocketTimeout):
                raise GeocoderTimedOut("Service timed out")
            elif isinstance(error, SSLError):
                if "timed out" in message:
                    raise GeocoderTimedOut("Service timed out")
            raise GeocoderServiceError(message)
        else:
            text = self._decode_page(page)
            status_code = page.getcode()
            if status_code >= 400:
                response_headers = {
                    name.lower(): value
                    for name, value in page.headers.items()
                }
                raise AdapterHTTPError(
                    "Non-successful status code %s" % status_code,
                    status_code=status_code,
                    headers=response_headers,
                    text=text,
                )

        return text

    def _read_http_error_body(self, error):
        try:
            return self._decode_page(error)
        except Exception:
            logger.debug(
                "Unable to fetch body for a non-successful HTTP response", exc_info=True
            )
            return None

    def _decode_page(self, page):
        encoding = page.headers.get_content_charset() or "utf-8"
        try:
            body_bytes = page.read()
        except Exception:
            raise GeocoderServiceError("Unable to read the response")

        try:
            return str(body_bytes, encoding=encoding)
        except ValueError:
            raise GeocoderParseError("Unable to decode the response bytes")


class RequestsAdapter(BaseSyncAdapter):
    """The adapter which uses `requests`_ library.

    .. _requests: https://requests.readthedocs.io

    `requests` supports keep-alives, retries, persists Cookies,
    allows response compression and uses HTTP/1.1 [currently].

    ``requests`` package must be installed in order to use this adapter.
    """

    is_available = requests_available

    def __init__(
        self,
        *,
        proxies,
        ssl_context,
        pool_connections=10,
        pool_maxsize=10,
        max_retries=2,
        pool_block=False
    ):
        if not requests_available:
            raise ImportError(
                "`requests` must be installed in order to use RequestsAdapter. "
                "If you have installed geopy via pip, you may use "
                "this command to install requests: "
                '`pip install "geopy[requests]"`.'
            )
        proxies = _normalize_proxies(proxies)
        super().__init__(proxies=proxies, ssl_context=ssl_context)

        self.session = requests.Session()
        self.session.trust_env = False  # don't use system proxies
        self.session.proxies = proxies

        self.session.mount(
            "http://",
            RequestsHTTPAdapter(
                pool_connections=pool_connections,
                pool_maxsize=pool_maxsize,
                max_retries=max_retries,
                pool_block=pool_block,
            ),
        )
        self.session.mount(
            "https://",
            RequestsHTTPWithSSLContextAdapter(
                ssl_context=ssl_context,
                pool_connections=pool_connections,
                pool_maxsize=pool_maxsize,
                max_retries=max_retries,
                pool_block=pool_block,
            ),
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def __del__(self):
        # Cleanup keepalive connections when Geocoder (and, thus, Adapter)
        # instances are getting garbage-collected.
        session = getattr(self, "session", None)
        if session is not None:
            try:
                session.close()
            except TypeError:
                # It's possible for the close method to try to fetch a
                # non-existent old_pool in urllib3 with a misleading state
                # ultimately due to stdlib queue/threading behaviour.
                # Since the error arises from a non-existent pool
                # (TypeError: 'NoneType' object is not callable)
                # it's safe to ignore this error
                pass

    def get_text(self, url, *, timeout, headers):
        resp = self._request(url, timeout=timeout, headers=headers)
        return resp.text

    def get_json(self, url, *, timeout, headers):
        resp = self._request(url, timeout=timeout, headers=headers)
        try:
            return resp.json()
        except ValueError:
            raise GeocoderParseError(
                "Could not deserialize using deserializer:\n%s" % resp.text
            )

    def _request(self, url, *, timeout, headers):
        try:
            resp = self.session.get(url, timeout=timeout, headers=headers)
        except Exception as error:
            message = str(error)
            if isinstance(error, SocketTimeout):
                raise GeocoderTimedOut("Service timed out")
            elif isinstance(error, SSLError):
                if "timed out" in message:
                    raise GeocoderTimedOut("Service timed out")
            elif isinstance(error, requests.ConnectionError):
                if "unauthorized" in message.lower():
                    raise GeocoderServiceError(message)
                else:
                    raise GeocoderUnavailable(message)
            elif isinstance(error, requests.Timeout):
                raise GeocoderTimedOut("Service timed out")
            raise GeocoderServiceError(message)
        else:
            if resp.status_code >= 400:
                raise AdapterHTTPError(
                    "Non-successful status code %s" % resp.status_code,
                    status_code=resp.status_code,
                    headers=resp.headers,
                    text=resp.text,
                )

        return resp


class AioHTTPAdapter(BaseAsyncAdapter):
    """The adapter which uses `aiohttp`_ library.

    .. _aiohttp: https://docs.aiohttp.org/

    `aiohttp` supports keep-alives, persists Cookies, allows response
    compression and uses HTTP/1.1 [currently].

    ``aiohttp`` package must be installed in order to use this adapter.
    """

    is_available = aiohttp_available

    def __init__(self, *, proxies, ssl_context):
        if not aiohttp_available:
            raise ImportError(
                "`aiohttp` must be installed in order to use AioHTTPAdapter. "
                "If you have installed geopy via pip, you may use "
                "this command to install aiohttp: "
                '`pip install "geopy[aiohttp]"`.'
            )
        proxies = _normalize_proxies(proxies)
        super().__init__(proxies=proxies, ssl_context=ssl_context)

        self.proxies = proxies
        self.ssl_context = ssl_context

    @property
    def session(self):
        # Lazy session creation, which allows to avoid "unclosed socket"
        # warnings if a Geocoder instance is created without entering
        # async context and making any requests.
        session = self.__dict__.get("session")
        if session is None:
            session = aiohttp.ClientSession(
                trust_env=False,  # don't use system proxies
                raise_for_status=False
            )
            self.__dict__["session"] = session
        return session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Might issue a warning if loop is immediately closed:
        #   ResourceWarning: unclosed transport <_SelectorSocketTransport fd=10>
        # https://github.com/aio-libs/aiohttp/issues/1115#issuecomment-242278593
        # https://github.com/python/asyncio/issues/466
        await self.session.close()

    async def get_text(self, url, *, timeout, headers):
        with self._normalize_exceptions():
            async with self._request(url, timeout=timeout, headers=headers) as resp:
                await self._raise_for_status(resp)
                return await resp.text()

    async def get_json(self, url, *, timeout, headers):
        with self._normalize_exceptions():
            async with self._request(url, timeout=timeout, headers=headers) as resp:
                await self._raise_for_status(resp)
                try:
                    try:
                        return await resp.json()
                    except aiohttp.client_exceptions.ContentTypeError:
                        # `Attempt to decode JSON with unexpected mimetype:
                        # text/plain;charset=utf-8`
                        return json.loads(await resp.text())
                except ValueError:
                    raise GeocoderParseError(
                        "Could not deserialize using deserializer:\n%s"
                        % (await resp.text())
                    )

    async def _raise_for_status(self, resp):
        if resp.status >= 400:
            raise AdapterHTTPError(
                "Non-successful status code %s" % resp.status,
                status_code=resp.status,
                headers=resp.headers,
                text=await resp.text(),
            )

    def _request(self, url, *, timeout, headers):
        if self.proxies:
            scheme = urlparse(url).scheme
            proxy = self.proxies.get(scheme.lower())
        else:
            proxy = None

        # aiohttp accepts url as string or as yarl.URL.
        # A string url might be re-encoded by yarl, which might cause
        # a hashsum of params to change. Some geocoders use that
        # to authenticate their requests (such as Baidu SK).
        url = yarl.URL(url, encoded=True)  # `encoded` param disables url re-encoding
        return self.session.get(
            url, timeout=timeout, headers=headers, proxy=proxy, ssl=self.ssl_context
        )

    @contextlib.contextmanager
    def _normalize_exceptions(self):
        try:
            yield
        except (GeopyError, AdapterHTTPError, AssertionError):
            raise
        except Exception as error:
            message = str(error)
            if isinstance(error, asyncio.TimeoutError):
                raise GeocoderTimedOut("Service timed out")
            elif isinstance(error, SSLError):
                if "timed out" in message:
                    raise GeocoderTimedOut("Service timed out")
            elif isinstance(error, aiohttp.ClientConnectionError):
                raise GeocoderUnavailable(message)
            raise GeocoderServiceError(message)


# https://github.com/kennethreitz/requests/issues/3774#issuecomment-267871876
class RequestsHTTPWithSSLContextAdapter(RequestsHTTPAdapter):
    def __init__(self, *, ssl_context=None, **kwargs):
        self.__ssl_context = ssl_context
        self.__urllib3_warned = False
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        if self.__ssl_context is not None:
            # This ssl context would get passed through the urllib3's
            # `PoolManager` up to the `HTTPSConnection` class.
            kwargs["ssl_context"] = self.__ssl_context
            self.__warn_if_old_urllib3()
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, proxy, **proxy_kwargs):
        if self.__ssl_context is not None:
            proxy_kwargs["ssl_context"] = self.__ssl_context
            self.__warn_if_old_urllib3()
        return super().proxy_manager_for(proxy, **proxy_kwargs)

    def __warn_if_old_urllib3(self):
        if self.__urllib3_warned:
            return

        self.__urllib3_warned = True

        try:
            import requests.packages.urllib3 as urllib3
        except ImportError:
            import urllib3

        def silent_int(s):
            try:
                return int(s)
            except ValueError:
                return 0

        version = tuple(silent_int(v) for v in urllib3.__version__.split("."))

        if version < (1, 24, 2):
            warnings.warn(
                "urllib3 prior to 1.24.2 is known to have a bug with "
                "custom ssl contexts: it attempts to load system certificates "
                "to them. Please consider upgrading `requests` and `urllib3` "
                "packages. See https://github.com/urllib3/urllib3/pull/1566",
                UserWarning,
            )

    def cert_verify(self, conn, url, verify, cert):
        super().cert_verify(conn, url, verify, cert)
        if self.__ssl_context is not None:
            # Stop requests from adding any certificates to the ssl context.
            conn.ca_certs = None
            conn.ca_cert_dir = None
            conn.cert_file = None
            conn.key_file = None
