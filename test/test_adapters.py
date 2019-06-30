import os
import ssl
import unittest
from contextlib import ExitStack
from unittest.mock import patch
from urllib.parse import urljoin
from urllib.request import getproxies, urlopen

import pytest

import geopy.geocoders
from geopy.adapters import AdapterHTTPError, URLLibAdapter
from geopy.exc import GeocoderParseError, GeocoderServiceError
from geopy.geocoders.base import Geocoder
from test.proxy_server import HttpServerThread, ProxyServerThread

CERT_SELFSIGNED_CA = os.path.join(os.path.dirname(__file__), 'selfsigned_ca.pem')

# Are system proxies set? System proxies are set in:
# - Environment variables (HTTP_PROXY/HTTPS_PROXY) on Unix;
# - System Configuration Framework on macOS;
# - Registry's Internet Settings section on Windows.
WITH_SYSTEM_PROXIES = bool(getproxies())


class DummyGeocoder(Geocoder):
    def geocode(self, location, *, is_json=False):
        geo_html = self._call_geocoder(location, is_json=is_json)
        return geo_html if geo_html else None


@pytest.mark.usefixtures("skip_if_internet_access_is_not_allowed")
class BaseSystemCATestCase:
    """Test TLS certificates validation using the system-trusted CAs.
    """
    adapter_factory = NotImplementedError  # overridden in subclasses

    remote_website_https = "https://httpbin.org/html"  # must be trusted by the system CAs
    timeout = 5

    def setUp(self):
        self.stack = ExitStack()
        self.proxy_server = self.stack.enter_context(
            ProxyServerThread(timeout=self.timeout)
        )
        self.stack.enter_context(
            patch.object(
                geopy.geocoders.options, 'default_adapter_factory', self.adapter_factory
            )
        )
        self.proxy_url = self.proxy_server.get_proxy_url()

    def tearDown(self):
        self.stack.close()

    def test_geocoder_constructor_uses_https_proxy(self):
        base_http = urlopen(self.remote_website_https, timeout=self.timeout)
        base_html = base_http.read().decode()

        geocoder_dummy = DummyGeocoder(proxies={"https": self.proxy_url},
                                       timeout=self.timeout)
        self.assertEqual(0, len(self.proxy_server.requests))
        self.assertEqual(
            base_html,
            geocoder_dummy.geocode(self.remote_website_https)
        )
        self.assertEqual(1, len(self.proxy_server.requests))

    def test_ssl_context_with_proxy_is_respected(self):
        # Create an ssl context which should not allow the negotiation with
        # the `self.remote_website_https`.
        bad_ctx = ssl.create_default_context(cafile=CERT_SELFSIGNED_CA)
        geocoder_dummy = DummyGeocoder(proxies={"https": self.proxy_url},
                                       ssl_context=bad_ctx,
                                       timeout=self.timeout)
        self.assertEqual(0, len(self.proxy_server.requests))
        with self.assertRaises(GeocoderServiceError) as cm:
            geocoder_dummy.geocode(self.remote_website_https)
        self.assertIn('SSL', str(cm.exception))
        self.assertEqual(1, len(self.proxy_server.requests))

    @unittest.skipUnless(not WITH_SYSTEM_PROXIES,
                         "There're active system proxies")
    def test_ssl_context_without_proxy_is_respected(self):
        # Create an ssl context which should not allow the negotiation with
        # the `self.remote_website_https`.
        bad_ctx = ssl.create_default_context(cafile=CERT_SELFSIGNED_CA)
        geocoder_dummy = DummyGeocoder(ssl_context=bad_ctx,
                                       timeout=self.timeout)
        with self.assertRaises(GeocoderServiceError) as cm:
            geocoder_dummy.geocode(self.remote_website_https)
        self.assertIn('SSL', str(cm.exception))


class BaseLocalProxyTestCase:
    """Proxy integration tests using a local (plaintext) HTTP server."""
    adapter_factory = NotImplementedError  # overridden in subclasses

    timeout = 5

    def setUp(self):
        self.stack = ExitStack()
        self.proxy_server = self.stack.enter_context(
            ProxyServerThread(timeout=self.timeout)
        )
        self.http_server = self.stack.enter_context(
            HttpServerThread(timeout=self.timeout)
        )
        self.stack.enter_context(
            patch.object(
                geopy.geocoders.options, 'default_adapter_factory', self.adapter_factory
            )
        )
        self.proxy_url = self.proxy_server.get_proxy_url()
        self.remote_website_http = self.http_server.get_server_url()
        self.remote_website_http_json = urljoin(self.remote_website_http, "/json")
        self.remote_website_http_404 = urljoin(self.remote_website_http, "/404")

    def tearDown(self):
        self.stack.close()

    def test_geocoder_constructor_uses_http_proxy(self):
        base_http = urlopen(self.remote_website_http, timeout=self.timeout)
        base_html = base_http.read().decode()

        geocoder_dummy = DummyGeocoder(proxies={"http": self.proxy_url},
                                       timeout=self.timeout)
        self.assertEqual(0, len(self.proxy_server.requests))
        self.assertEqual(
            base_html,
            geocoder_dummy.geocode(self.remote_website_http)
        )
        self.assertEqual(1, len(self.proxy_server.requests))

    def test_geocoder_constructor_uses_str_proxy(self):
        base_http = urlopen(self.remote_website_http, timeout=self.timeout)
        base_html = base_http.read().decode()
        geocoder_dummy = DummyGeocoder(proxies=self.proxy_url,
                                       timeout=self.timeout)
        self.assertEqual(0, len(self.proxy_server.requests))
        self.assertEqual(
            base_html,
            geocoder_dummy.geocode(self.remote_website_http)
        )
        self.assertEqual(1, len(self.proxy_server.requests))

    def test_geocoder_constructor_has_both_schemes_proxy(self):
        g = DummyGeocoder(proxies=self.proxy_url, scheme='http')
        self.assertDictEqual(g.proxies, {'http': self.proxy_url,
                                         'https': self.proxy_url})

    def test_get_json(self):
        geocoder_dummy = DummyGeocoder(timeout=self.timeout)
        result = geocoder_dummy.geocode(self.remote_website_http_json, is_json=True)
        assert isinstance(result, dict)

    def test_get_json_failure_on_non_json(self):
        geocoder_dummy = DummyGeocoder(timeout=self.timeout)
        with self.assertRaises(GeocoderParseError):
            geocoder_dummy.geocode(self.remote_website_http, is_json=True)

    def test_adapter_exception_for_non_200_response(self):
        geocoder_dummy = DummyGeocoder(timeout=self.timeout)
        with self.assertRaises(GeocoderServiceError) as cm:
            geocoder_dummy.geocode(self.remote_website_http_404)
        self.assertIsInstance(cm.exception, GeocoderServiceError)
        self.assertIsInstance(cm.exception.__cause__, AdapterHTTPError)
        self.assertIsInstance(cm.exception.__cause__, IOError)


@unittest.skipUnless(not WITH_SYSTEM_PROXIES,
                     "There're active system proxies")
class BaseSystemProxiesTestCase:
    """Tests checking that system proxies are respected."""
    adapter_factory = None  # overridden in subclasses

    timeout = 5

    def setUp(self):
        self.stack = ExitStack()
        self.proxy_server = self.stack.enter_context(
            ProxyServerThread(timeout=self.timeout)
        )
        self.http_server = self.stack.enter_context(
            HttpServerThread(timeout=self.timeout)
        )
        self.stack.enter_context(
            patch.object(
                geopy.geocoders.options, 'default_adapter_factory', self.adapter_factory
            )
        )

        self.proxy_url = self.proxy_server.get_proxy_url()
        self.remote_website_http = self.http_server.get_server_url()

        self.assertIsNone(os.environ.get('http_proxy'))
        self.assertIsNone(os.environ.get('https_proxy'))
        os.environ['http_proxy'] = self.proxy_url
        os.environ['https_proxy'] = self.proxy_url

    def tearDown(self):
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)
        self.stack.close()

    def test_system_proxies_are_respected_by_default(self):
        geocoder_dummy = DummyGeocoder(timeout=self.timeout)
        self.assertEqual(0, len(self.proxy_server.requests))
        geocoder_dummy.geocode(self.remote_website_http)
        self.assertEqual(1, len(self.proxy_server.requests))

    def test_system_proxies_are_respected_with_none(self):
        # proxies=None means "use system proxies", e.g. from the ENV.
        geocoder_dummy = DummyGeocoder(proxies=None, timeout=self.timeout)
        self.assertEqual(0, len(self.proxy_server.requests))
        geocoder_dummy.geocode(self.remote_website_http)
        self.assertEqual(1, len(self.proxy_server.requests))

    def test_system_proxies_are_reset_with_empty_dict(self):
        geocoder_dummy = DummyGeocoder(proxies={}, timeout=self.timeout)
        self.assertEqual(0, len(self.proxy_server.requests))
        geocoder_dummy.geocode(self.remote_website_http)
        self.assertEqual(0, len(self.proxy_server.requests))

    def test_string_value_overrides_system_proxies(self):
        os.environ['http_proxy'] = '127.0.0.1:1'
        os.environ['https_proxy'] = '127.0.0.1:1'

        geocoder_dummy = DummyGeocoder(proxies=self.proxy_url,
                                       timeout=self.timeout)
        self.assertEqual(0, len(self.proxy_server.requests))
        geocoder_dummy.geocode(self.remote_website_http)
        self.assertEqual(1, len(self.proxy_server.requests))


class URLLibAdapterSystemCATestCase(BaseSystemCATestCase, unittest.TestCase):
    adapter_factory = URLLibAdapter


class URLLibAdapterLocalProxyTestCase(BaseLocalProxyTestCase, unittest.TestCase):
    adapter_factory = URLLibAdapter


class URLLibAdapterSystemProxiesTestCase(BaseSystemProxiesTestCase, unittest.TestCase):
    adapter_factory = URLLibAdapter
