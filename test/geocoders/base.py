
import unittest
from mock import patch
import warnings

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

        geocoder = Geocoder(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
        )
        for attr in ('format_string', 'scheme', 'timeout', 'proxies'):
            self.assertEqual(locals()[attr], getattr(geocoder, attr))
        self.assertEqual(user_agent, geocoder.headers['User-Agent'])

    def test_init_with_defaults(self):
        attr_to_option = {
            'format_string': 'default_format_string',
            'scheme': 'default_scheme',
            'timeout': 'default_timeout',
            'proxies': 'default_proxies',
        }

        geocoder = Geocoder()
        for geocoder_attr, options_attr in attr_to_option.items():
            self.assertEqual(getattr(geopy.geocoders.options, options_attr),
                             getattr(geocoder, geocoder_attr))
        self.assertEqual(geopy.geocoders.options.default_user_agent,
                         geocoder.headers['User-Agent'])

    @patch.object(geopy.geocoders.options, 'default_proxies', {'https': '192.0.2.0'})
    @patch.object(geopy.geocoders.options, 'default_timeout', 10)
    def test_init_with_none_overrides_default(self):
        geocoder = Geocoder(proxies=None, timeout=None)
        self.assertIsNone(geocoder.proxies)
        self.assertIsNone(geocoder.timeout)

    @patch.object(geopy.geocoders.options, 'default_user_agent', 'mocked_user_agent/0.0.0')
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

        with patch.object(g, 'urlopen') as mock_urlopen:
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
