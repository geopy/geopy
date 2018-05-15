
import unittest
from mock import patch, sentinel
import warnings

import geopy.compat
import geopy.geocoders
from geopy.exc import GeocoderNotFound
from geopy.geocoders import GoogleV3, get_geocoder_for_service
from geopy.geocoders.base import Geocoder
from geopy.point import Point


class GetGeocoderTestCase(unittest.TestCase):

    def test_ok(self):
        """
        get_geocoder_for_service
        """
        self.assertEqual(get_geocoder_for_service("google"), GoogleV3)
        self.assertEqual(get_geocoder_for_service("googlev3"), GoogleV3)

    def test_fail(self):
        """
        get_geocoder_for_service unknown service
        """
        with self.assertRaises(GeocoderNotFound):
            get_geocoder_for_service("")


class GeocoderTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Geocoder()
        cls.coordinates = (40.74113, -73.989656)
        cls.coordinates_str = "40.74113,-73.989656"
        cls.coordinates_address = "175 5th Avenue, NYC, USA"

    def test_init_with_args(self):
        format_string = '%s Los Angeles, CA USA'
        scheme = 'http'
        timeout = 942
        proxies = {'https': '192.0.2.0'}
        user_agent = 'test app'
        ssl_context = sentinel.some_ssl_context

        geocoder = Geocoder(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )
        for attr in ('format_string', 'scheme', 'timeout', 'proxies',
                     'ssl_context'):
            self.assertEqual(locals()[attr], getattr(geocoder, attr))
        self.assertEqual(user_agent, geocoder.headers['User-Agent'])

    def test_init_with_defaults(self):
        attr_to_option = {
            'format_string': 'default_format_string',
            'scheme': 'default_scheme',
            'timeout': 'default_timeout',
            'proxies': 'default_proxies',
            'ssl_context': 'default_ssl_context',
        }

        geocoder = Geocoder()
        for geocoder_attr, options_attr in attr_to_option.items():
            self.assertEqual(getattr(geopy.geocoders.options, options_attr),
                             getattr(geocoder, geocoder_attr))
        self.assertEqual(geopy.geocoders.options.default_user_agent,
                         geocoder.headers['User-Agent'])

    @patch.object(geopy.geocoders.options, 'default_proxies', {'https': '192.0.2.0'})
    @patch.object(geopy.geocoders.options, 'default_timeout', 10)
    @patch.object(geopy.geocoders.options, 'default_ssl_context',
                  sentinel.some_ssl_context)
    def test_init_with_none_overrides_default(self):
        geocoder = Geocoder(proxies=None, timeout=None, ssl_context=None)
        self.assertIsNone(geocoder.proxies)
        self.assertIsNone(geocoder.timeout)
        self.assertIsNone(geocoder.ssl_context)

    @patch.object(geopy.geocoders.options, 'default_user_agent',
                  'mocked_user_agent/0.0.0')
    def test_user_agent_default(self):
        geocoder = Geocoder()
        self.assertEqual(geocoder.headers['User-Agent'],
                         'mocked_user_agent/0.0.0')

    def test_user_agent_custom(self):
        geocoder = Geocoder(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    @patch.object(geopy.geocoders.options, 'default_timeout', 12)
    def test_call_geocoder_timeout(self):
        url = 'spam://ham/eggs'

        g = Geocoder()
        self.assertEqual(g.timeout, 12)

        # Suppress another (unrelated) warning when running tests on an old Python.
        with patch('geopy.compat._URLLIB_SUPPORTS_SSL_CONTEXT', True), \
                patch.object(g, 'urlopen') as mock_urlopen:
            g._call_geocoder(url, raw=True)
            args, kwargs = mock_urlopen.call_args
            self.assertEqual(kwargs['timeout'], 12)

            g._call_geocoder(url, timeout=7, raw=True)
            args, kwargs = mock_urlopen.call_args
            self.assertEqual(kwargs['timeout'], 7)

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                g._call_geocoder(url, timeout=None, raw=True)
                args, kwargs = mock_urlopen.call_args
                self.assertEqual(kwargs['timeout'], 12)
                self.assertEqual(1, len(w))

    def test_ssl_context_for_old_python(self):
        # Before (exclusive) 2.7.9 and 3.4.3.

        # Keep the reference, because `geopy.compat.HTTPSHandler` will be
        # mocked below.
        orig_HTTPSHandler = geopy.compat.HTTPSHandler

        class HTTPSHandlerStub(geopy.compat.HTTPSHandler):
            def __init__(self):  # No `context` arg.
                orig_HTTPSHandler.__init__(self)

        if hasattr(geopy.compat, '__warningregistry__'):
            # If running tests on an old Python, the warning we are going
            # to test might have been already issued and recorded in
            # the registry. Clean it up, so we could receive the warning again.
            del geopy.compat.__warningregistry__

        with patch('geopy.compat._URLLIB_SUPPORTS_SSL_CONTEXT',
                   geopy.compat._is_urllib_context_supported(HTTPSHandlerStub)), \
                patch('geopy.compat.HTTPSHandler', HTTPSHandlerStub), \
                warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            self.assertFalse(geopy.compat._URLLIB_SUPPORTS_SSL_CONTEXT)

            self.assertEqual(0, len(w))
            Geocoder()
            self.assertEqual(1, len(w))

    def test_ssl_context_for_newer_python(self):
        # From (inclusive) 2.7.9 and 3.4.3.

        # Keep the reference, because `geopy.compat.HTTPSHandler` will be
        # mocked below.
        orig_HTTPSHandler = geopy.compat.HTTPSHandler

        class HTTPSHandlerStub(geopy.compat.HTTPSHandler):
            def __init__(self, context=None):
                orig_HTTPSHandler.__init__(self)

        if hasattr(geopy.compat, '__warningregistry__'):
            # If running tests on an old Python, the warning we are going
            # to test might have been already issued and recorded in
            # the registry. Clean it up, so we could receive the warning again.
            del geopy.compat.__warningregistry__

        with patch('geopy.compat._URLLIB_SUPPORTS_SSL_CONTEXT',
                   geopy.compat._is_urllib_context_supported(HTTPSHandlerStub)), \
                patch('geopy.compat.HTTPSHandler', HTTPSHandlerStub), \
                patch.object(HTTPSHandlerStub, '__init__', autospec=True,
                             side_effect=HTTPSHandlerStub.__init__
                             ) as mock_https_handler_init, \
                warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            self.assertTrue(geopy.compat._URLLIB_SUPPORTS_SSL_CONTEXT)

            for ssl_context in (None, sentinel.some_ssl_context):
                mock_https_handler_init.reset_mock()
                Geocoder(ssl_context=ssl_context)
                args, kwargs = mock_https_handler_init.call_args
                self.assertIs(kwargs['context'], ssl_context)
            self.assertEqual(0, len(w))

    def test_point_coercion_point(self):
        """
        Geocoder._coerce_point_to_string Point
        """
        self.assertEqual(
            self.geocoder._coerce_point_to_string(Point(*self.coordinates)),
            self.coordinates_str
        )

    def test_point_coercion_floats(self):
        """
        Geocoder._coerce_point_to_string tuple of coordinates
        """
        self.assertEqual(
            self.geocoder._coerce_point_to_string(self.coordinates),
            self.coordinates_str
        )

    def test_point_coercion_string(self):
        """
        Geocoder._coerce_point_to_string string of coordinates
        """
        self.assertEqual(
            self.geocoder._coerce_point_to_string(self.coordinates_str),
            self.coordinates_str
        )

    def test_point_coercion_address(self):
        """
        Geocoder._coerce_point_to_string address string
        """
        self.assertEqual(
            self.geocoder._coerce_point_to_string(self.coordinates_address),
            self.coordinates_address
        )
