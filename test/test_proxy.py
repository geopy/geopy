"""
Test ability to proxy requests.
"""
import unittest
from test.proxy_server import ProxyServerThread

from geopy.compat import urlopen
from geopy.geocoders.base import Geocoder


class DummyGeocoder(Geocoder):
    def geocode(self, location):
        geo_request = self.urlopen(location, timeout=self.timeout)
        geo_html = geo_request.read()
        return geo_html if geo_html else None


class ProxyTestCase(unittest.TestCase): # pylint: disable=R0904,C0111
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
        self.assertTrue(
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
        self.assertTrue(
            base_html,
            geocoder_dummy.geocode(self.remote_website_https)
        )
        self.assertEqual(1, len(self.proxy_server.requests))
