import contextlib
import os
import ssl
from unittest.mock import patch
from urllib.parse import urljoin
from urllib.request import getproxies, urlopen

import pytest

import geopy.geocoders
from geopy.adapters import (
    AdapterHTTPError,
    AioHTTPAdapter,
    BaseAsyncAdapter,
    RequestsAdapter,
    URLLibAdapter,
)
from geopy.exc import (
    GeocoderAuthenticationFailure,
    GeocoderParseError,
    GeocoderServiceError,
)
from geopy.geocoders.base import Geocoder
from test.proxy_server import HttpServerThread, ProxyServerThread

CERT_SELFSIGNED_CA = os.path.join(os.path.dirname(__file__), "..", "selfsigned_ca.pem")

# Are system proxies set? System proxies are set in:
# - Environment variables (HTTP_PROXY/HTTPS_PROXY) on Unix;
# - System Configuration Framework on macOS;
# - Registry's Internet Settings section on Windows.
WITH_SYSTEM_PROXIES = bool(getproxies())

AVAILABLE_ADAPTERS = [URLLibAdapter]
NOT_AVAILABLE_ADAPTERS = []

try:
    import requests  # noqa
except ImportError:
    NOT_AVAILABLE_ADAPTERS.append(RequestsAdapter)
else:
    AVAILABLE_ADAPTERS.append(RequestsAdapter)

try:
    import aiohttp  # noqa
except ImportError:
    NOT_AVAILABLE_ADAPTERS.append(AioHTTPAdapter)
else:
    AVAILABLE_ADAPTERS.append(AioHTTPAdapter)


class DummyGeocoder(Geocoder):
    def geocode(self, location, *, is_json=False):
        return self._call_geocoder(location, lambda res: res, is_json=is_json)


@pytest.fixture(scope="session")
def timeout():
    return 5


@pytest.fixture(scope="session")
def proxy_server_thread(timeout):
    with ProxyServerThread(timeout=timeout) as proxy_server:
        yield proxy_server


@pytest.fixture
def proxy_server(proxy_server_thread):
    proxy_server_thread.reset()
    return proxy_server_thread


@pytest.fixture(params=[True, False])
def proxy_url(request, proxy_server):
    # Parametrize with proxy urls with and without scheme, e.g.
    # - `http://localhost:8080`
    # - `localhost:8080`
    with_scheme = request.param
    return proxy_server.get_proxy_url(with_scheme)


@pytest.mark.skipif(WITH_SYSTEM_PROXIES, reason="There're active system proxies")
@pytest.fixture
def inject_proxy_to_system_env(proxy_url):
    assert os.environ.get("http_proxy") is None
    assert os.environ.get("https_proxy") is None
    os.environ["http_proxy"] = proxy_url
    os.environ["https_proxy"] = proxy_url

    yield

    os.environ.pop("http_proxy", None)
    os.environ.pop("https_proxy", None)


@pytest.fixture(scope="session")
def http_server(timeout):
    with HttpServerThread(timeout=timeout) as http_server:
        yield http_server


@pytest.fixture
def remote_website_trusted_https(skip_if_internet_access_is_not_allowed):
    return "https://httpbingo.org/html"  # must be trusted by the system CAs


@pytest.fixture
def remote_website_http(http_server):
    return http_server.get_server_url()


@pytest.fixture
def remote_website_http_json(remote_website_http):
    return urljoin(remote_website_http, "/json")


@pytest.fixture
def remote_website_http_json_plain(remote_website_http):
    return urljoin(remote_website_http, "/json/plain")


@pytest.fixture
def remote_website_http_404(remote_website_http):
    return urljoin(remote_website_http, "/404")


@pytest.fixture(params=AVAILABLE_ADAPTERS, autouse=True)
def adapter_factory(request):
    adapter_factory = request.param
    with patch.object(
        geopy.geocoders.options, "default_adapter_factory", adapter_factory
    ):
        yield adapter_factory


@contextlib.asynccontextmanager
async def make_dummy_async_geocoder(**kwargs):
    geocoder = DummyGeocoder(**kwargs)
    run_async = isinstance(geocoder.adapter, BaseAsyncAdapter)
    if run_async:
        async with geocoder:
            yield geocoder
    else:
        orig_geocode = geocoder.geocode

        async def geocode(*args, **kwargs):
            return orig_geocode(*args, **kwargs)

        geocoder.geocode = geocode
        yield geocoder


@pytest.mark.parametrize("adapter_cls", NOT_AVAILABLE_ADAPTERS)
async def test_not_available_adapters_raise(adapter_cls):
    # Note: this test is uselessly parametrized with `adapter_factory`.
    with patch.object(
        geopy.geocoders.options, "default_adapter_factory", adapter_cls
    ):
        with pytest.raises(ImportError):
            async with make_dummy_async_geocoder():
                pass


async def test_geocoder_constructor_uses_https_proxy(
    timeout, proxy_server, proxy_url, remote_website_trusted_https
):
    base_http = urlopen(remote_website_trusted_https, timeout=timeout)
    base_html = base_http.read().decode()

    async with make_dummy_async_geocoder(
        proxies={"https": proxy_url}, timeout=timeout
    ) as geocoder_dummy:
        assert 0 == len(proxy_server.requests)
        assert base_html == await geocoder_dummy.geocode(remote_website_trusted_https)
        assert 1 == len(proxy_server.requests)


@pytest.mark.parametrize("with_scheme", [False, True])
async def test_geocoder_http_proxy_auth_is_respected(
    timeout, proxy_server, remote_website_http, with_scheme
):
    proxy_server.set_auth("user", "test")
    base_http = urlopen(remote_website_http, timeout=timeout)
    base_html = base_http.read().decode()

    proxy_url = proxy_server.get_proxy_url(with_scheme=with_scheme)

    async with make_dummy_async_geocoder(
        proxies={"http": proxy_url}, timeout=timeout
    ) as geocoder_dummy:
        assert 0 == len(proxy_server.requests)
        assert base_html == await geocoder_dummy.geocode(remote_website_http)
        assert 1 == len(proxy_server.requests)


@pytest.mark.parametrize("with_scheme", [False, True])
async def test_geocoder_https_proxy_auth_is_respected(
    timeout, proxy_server, remote_website_trusted_https, with_scheme
):
    proxy_server.set_auth("user", "test")
    base_http = urlopen(remote_website_trusted_https, timeout=timeout)
    base_html = base_http.read().decode()

    proxy_url = proxy_server.get_proxy_url(with_scheme=with_scheme)

    async with make_dummy_async_geocoder(
        proxies={"https": proxy_url}, timeout=timeout
    ) as geocoder_dummy:
        assert 0 == len(proxy_server.requests)
        assert base_html == await geocoder_dummy.geocode(remote_website_trusted_https)
        assert 1 == len(proxy_server.requests)


async def test_geocoder_http_proxy_auth_error(
    timeout, proxy_server, proxy_url, remote_website_http
):
    # Set up proxy auth but query it without auth:
    proxy_server.set_auth("user", "test")

    async with make_dummy_async_geocoder(
        proxies={"http": proxy_url}, timeout=timeout
    ) as geocoder_dummy:
        # For HTTP targets we cannot distinguish between 401 from proxy
        # and 401 from geocoding service, thus the same error as for
        # 401 for geocoders is raised: GeocoderAuthenticationFailure
        with pytest.raises(GeocoderAuthenticationFailure) as exc_info:
            await geocoder_dummy.geocode(remote_website_http)
        assert exc_info.type is GeocoderAuthenticationFailure


async def test_geocoder_https_proxy_auth_error(
    timeout, proxy_server, proxy_url, remote_website_trusted_https
):
    # Set up proxy auth but query it without auth:
    proxy_server.set_auth("user", "test")

    async with make_dummy_async_geocoder(
        proxies={"https": proxy_url}, timeout=timeout
    ) as geocoder_dummy:
        with pytest.raises(GeocoderServiceError) as exc_info:
            await geocoder_dummy.geocode(remote_website_trusted_https)
        assert exc_info.type is GeocoderServiceError


async def test_ssl_context_with_proxy_is_respected(
    timeout, proxy_server, proxy_url, remote_website_trusted_https
):
    # Create an ssl context which should not allow the negotiation with
    # the `self.remote_website_https`.
    bad_ctx = ssl.create_default_context(cafile=CERT_SELFSIGNED_CA)
    async with make_dummy_async_geocoder(
        proxies={"https": proxy_url}, ssl_context=bad_ctx, timeout=timeout
    ) as geocoder_dummy:
        assert 0 == len(proxy_server.requests)
        with pytest.raises(GeocoderServiceError) as excinfo:
            await geocoder_dummy.geocode(remote_website_trusted_https)
        assert "SSL" in str(excinfo.value)
        assert 1 <= len(proxy_server.requests)


@pytest.mark.skipif(WITH_SYSTEM_PROXIES, reason="There're active system proxies")
async def test_ssl_context_without_proxy_is_respected(
    timeout, remote_website_trusted_https
):
    # Create an ssl context which should not allow the negotiation with
    # the `self.remote_website_https`.
    bad_ctx = ssl.create_default_context(cafile=CERT_SELFSIGNED_CA)
    async with make_dummy_async_geocoder(
        ssl_context=bad_ctx, timeout=timeout
    ) as geocoder_dummy:
        with pytest.raises(GeocoderServiceError) as excinfo:
            await geocoder_dummy.geocode(remote_website_trusted_https)
        assert "SSL" in str(excinfo.value)


async def test_geocoder_constructor_uses_http_proxy(
    timeout, proxy_server, proxy_url, remote_website_http
):
    base_http = urlopen(remote_website_http, timeout=timeout)
    base_html = base_http.read().decode()

    async with make_dummy_async_geocoder(
        proxies={"http": proxy_url}, timeout=timeout
    ) as geocoder_dummy:
        assert 0 == len(proxy_server.requests)
        assert base_html == await geocoder_dummy.geocode(remote_website_http)
        assert 1 == len(proxy_server.requests)


async def test_geocoder_constructor_uses_str_proxy(
    timeout, proxy_server, proxy_url, remote_website_http
):
    base_http = urlopen(remote_website_http, timeout=timeout)
    base_html = base_http.read().decode()

    async with make_dummy_async_geocoder(
        proxies=proxy_url, timeout=timeout
    ) as geocoder_dummy:
        assert 0 == len(proxy_server.requests)
        assert base_html == await geocoder_dummy.geocode(remote_website_http)
        assert 1 == len(proxy_server.requests)


async def test_geocoder_constructor_has_both_schemes_proxy(proxy_url):
    g = DummyGeocoder(proxies=proxy_url, scheme="http")
    assert g.proxies == {"http": proxy_url, "https": proxy_url}


async def test_get_json(remote_website_http_json, timeout):
    async with make_dummy_async_geocoder(timeout=timeout) as geocoder_dummy:
        result = await geocoder_dummy.geocode(remote_website_http_json, is_json=True)
        assert isinstance(result, dict)


async def test_get_json_plain(remote_website_http_json_plain, timeout):
    async with make_dummy_async_geocoder(timeout=timeout) as geocoder_dummy:
        result = await geocoder_dummy.geocode(
            remote_website_http_json_plain, is_json=True
        )
        assert isinstance(result, dict)


async def test_get_json_failure_on_non_json(remote_website_http, timeout):
    async with make_dummy_async_geocoder(timeout=timeout) as geocoder_dummy:
        with pytest.raises(GeocoderParseError):
            await geocoder_dummy.geocode(remote_website_http, is_json=True)


async def test_adapter_exception_for_non_200_response(remote_website_http_404, timeout):
    async with make_dummy_async_geocoder(timeout=timeout) as geocoder_dummy:
        with pytest.raises(GeocoderServiceError) as excinfo:
            await geocoder_dummy.geocode(remote_website_http_404)
        assert isinstance(excinfo.value, GeocoderServiceError)
        assert isinstance(excinfo.value.__cause__, AdapterHTTPError)
        assert isinstance(excinfo.value.__cause__, IOError)

        adapter_http_error = excinfo.value.__cause__
        assert adapter_http_error.status_code == 404
        assert adapter_http_error.headers['x-test-header'] == 'hello'
        assert adapter_http_error.text == 'Not found'


async def test_system_proxies_are_respected_by_default(
    inject_proxy_to_system_env,
    timeout,
    proxy_server,
    remote_website_http,
    adapter_factory,
    proxy_url,
):
    async with make_dummy_async_geocoder(timeout=timeout) as geocoder_dummy:
        assert 0 == len(proxy_server.requests)
        await geocoder_dummy.geocode(remote_website_http)
        assert 1 == len(proxy_server.requests)


async def test_system_proxies_are_respected_with_none(
    inject_proxy_to_system_env,
    timeout,
    proxy_server,
    remote_website_http,
    adapter_factory,
    proxy_url,
):
    # proxies=None means "use system proxies", e.g. from the ENV.
    async with make_dummy_async_geocoder(
        proxies=None, timeout=timeout
    ) as geocoder_dummy:
        assert 0 == len(proxy_server.requests)
        await geocoder_dummy.geocode(remote_website_http)
        assert 1 == len(proxy_server.requests)


async def test_system_proxies_are_reset_with_empty_dict(
    inject_proxy_to_system_env, timeout, proxy_server, remote_website_http
):
    async with make_dummy_async_geocoder(proxies={}, timeout=timeout) as geocoder_dummy:
        assert 0 == len(proxy_server.requests)
        await geocoder_dummy.geocode(remote_website_http)
        assert 0 == len(proxy_server.requests)


async def test_string_value_overrides_system_proxies(
    inject_proxy_to_system_env, timeout, proxy_server, proxy_url, remote_website_http
):
    os.environ["http_proxy"] = "localhost:1"
    os.environ["https_proxy"] = "localhost:1"

    async with make_dummy_async_geocoder(
        proxies=proxy_url, timeout=timeout
    ) as geocoder_dummy:
        assert 0 == len(proxy_server.requests)
        await geocoder_dummy.geocode(remote_website_http)
        assert 1 == len(proxy_server.requests)
