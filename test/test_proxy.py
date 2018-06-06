"""
Test ability to proxy requests.
"""
import os
import ssl
import unittest
from test.proxy_server import ProxyServerThread

from geopy.compat import urlopen
from geopy.exc import GeocoderServiceError
from geopy.geocoders.base import Geocoder

CERT_SELFSIGNED_CA = os.path.join(os.path.dirname(__file__), 'selfsigned_ca.pem')


class DummyGeocoder(Geocoder):
    def geocode(self, location):
        geo_request = self._call_geocoder(location, raw=True)
        geo_html = geo_request.read()
        return geo_html if geo_html else None


class ProxyTestCase(unittest.TestCase):
    remote_website_http = "http://example.org/"
    remote_website_https = "https://example.org/"
    timeout = 5

    def setUp(self):
        self.proxy_server = ProxyServerThread(timeout=self.timeout)
        self.proxy_server.start()
        self.proxy_url = self.proxy_server.get_proxy_url()

    def tearDown(self):
        self.proxy_server.stop()
        self.proxy_server.join()

    def test_geocoder_constructor_uses_http_proxy(self):
        base_http = urlopen(self.remote_website_http, timeout=self.timeout)
        base_html = base_http.read()

        geocoder_dummy = DummyGeocoder(proxies={"http": self.proxy_url},
                                       timeout=self.timeout)
        self.assertEqual(0, len(self.proxy_server.requests))
        self.assertEqual(
            base_html,
            geocoder_dummy.geocode(self.remote_website_http)
        )
        self.assertEqual(1, len(self.proxy_server.requests))

    def test_geocoder_constructor_uses_https_proxy(self):
        base_http = urlopen(self.remote_website_https, timeout=self.timeout)
        base_html = base_http.read()

        geocoder_dummy = DummyGeocoder(proxies={"https": self.proxy_url},
                                       timeout=self.timeout)
        self.assertEqual(0, len(self.proxy_server.requests))
        self.assertEqual(
            base_html,
            geocoder_dummy.geocode(self.remote_website_https)
        )
        self.assertEqual(1, len(self.proxy_server.requests))

    @unittest.skipUnless(
        hasattr(ssl, 'create_default_context'),
        "The current Python version doesn't support `ssl.create_default_context`."
    )
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

    def test_geocoder_constructor_uses_str_http_proxy(self):
        base_http = urlopen(self.remote_website_http, timeout=self.timeout)
        base_html = base_http.read()
        geocoder_dummy = DummyGeocoder(proxies=self.proxy_url, scheme='http',
                                       timeout=self.timeout)
        print(geocoder_dummy.scheme, geocoder_dummy.proxies, 'proxy')
        self.assertEqual(0, len(self.proxy_server.requests))
        self.assertEqual(
            base_html,
            geocoder_dummy.geocode(self.remote_website_http)
        )
        self.assertEqual(1, len(self.proxy_server.requests))

    def test_geocoder_constructor_uses_str_https_proxy(self):
        base_http = urlopen(self.remote_website_https, timeout=self.timeout)
        base_html = base_http.read()

        geocoder_dummy = DummyGeocoder(proxies=self.proxy_url,
                                       timeout=self.timeout)
        self.assertEqual(0, len(self.proxy_server.requests))
        self.assertEqual(
            base_html,
            geocoder_dummy.geocode(self.remote_website_https)
        )
        self.assertEqual(1, len(self.proxy_server.requests))
