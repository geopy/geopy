import unittest
import warnings

import pytest
from mock import patch, sentinel

import geopy.compat
import geopy.geocoders
from geopy.exc import GeocoderNotFound, GeocoderQueryError
from geopy.geocoders import GoogleV3, get_geocoder_for_service
from geopy.geocoders.base import Geocoder
from geopy.point import Point


class GetGeocoderTestCase(unittest.TestCase):

    def test_get_geocoder_for_service(self):
        assert get_geocoder_for_service("google") == GoogleV3
        assert get_geocoder_for_service("googlev3") == GoogleV3

    def test_get_geocoder_for_service_raises_for_unknown(self):
        with pytest.raises(GeocoderNotFound):
            get_geocoder_for_service("")


class GeocoderTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Geocoder()

    def test_init_with_args(self):
        scheme = 'http'
        timeout = 942
        proxies = {'https': '192.0.2.0'}
        user_agent = 'test app'
        ssl_context = sentinel.some_ssl_context

        geocoder = Geocoder(
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )
        for attr in ('scheme', 'timeout', 'proxies', 'ssl_context'):
            assert locals()[attr] == getattr(geocoder, attr)
        assert user_agent == geocoder.headers['User-Agent']

    def test_deprecated_format_string(self):
        format_string = '%s Los Angeles, CA USA'

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            geocoder = Geocoder(
                format_string=format_string,
            )
            assert format_string == geocoder.format_string
            assert 1 == len(w)

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
            assert (
                getattr(geopy.geocoders.options, options_attr) ==
                getattr(geocoder, geocoder_attr)
            )
        assert (
            geopy.geocoders.options.default_user_agent ==
            geocoder.headers['User-Agent']
        )

    @patch.object(geopy.geocoders.options, 'default_proxies', {'https': '192.0.2.0'})
    @patch.object(geopy.geocoders.options, 'default_timeout', 10)
    @patch.object(geopy.geocoders.options, 'default_ssl_context',
                  sentinel.some_ssl_context)
    def test_init_with_none_overrides_default(self):
        geocoder = Geocoder(proxies=None, timeout=None, ssl_context=None)
        assert geocoder.proxies is None
        assert geocoder.timeout is None
        assert geocoder.ssl_context is None

    @patch.object(geopy.geocoders.options, 'default_user_agent',
                  'mocked_user_agent/0.0.0')
    def test_user_agent_default(self):
        geocoder = Geocoder()
        assert geocoder.headers['User-Agent'] == 'mocked_user_agent/0.0.0'

    def test_user_agent_custom(self):
        geocoder = Geocoder(
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    @patch.object(geopy.geocoders.options, 'default_timeout', 12)
    def test_call_geocoder_timeout(self):
        url = 'spam://ham/eggs'

        g = Geocoder()
        assert g.timeout == 12

        # Suppress another (unrelated) warning when running tests on an old Python.
        with patch('geopy.compat._URLLIB_SUPPORTS_SSL_CONTEXT', True), \
                patch.object(g, 'urlopen') as mock_urlopen:
            g._call_geocoder(url, raw=True)
            args, kwargs = mock_urlopen.call_args
            assert kwargs['timeout'] == 12

            g._call_geocoder(url, timeout=7, raw=True)
            args, kwargs = mock_urlopen.call_args
            assert kwargs['timeout'] == 7

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                g._call_geocoder(url, timeout=None, raw=True)
                args, kwargs = mock_urlopen.call_args
                assert kwargs['timeout'] == 12
                assert 1 == len(w)

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
            assert not geopy.compat._URLLIB_SUPPORTS_SSL_CONTEXT

            assert 0 == len(w)
            Geocoder()
            assert 1 == len(w)

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
            assert geopy.compat._URLLIB_SUPPORTS_SSL_CONTEXT

            for ssl_context in (None, sentinel.some_ssl_context):
                mock_https_handler_init.reset_mock()
                Geocoder(ssl_context=ssl_context)
                args, kwargs = mock_https_handler_init.call_args
                assert kwargs['context'] is ssl_context
            assert 0 == len(w)


class GeocoderPointCoercionTestCase(unittest.TestCase):
    coordinates = (40.74113, -73.989656)
    coordinates_str = "40.74113,-73.989656"
    coordinates_address = "175 5th Avenue, NYC, USA"

    def setUp(self):
        self.method = Geocoder._coerce_point_to_string

    def test_point(self):
        latlon = self.method(Point(*self.coordinates))
        assert latlon == self.coordinates_str

    def test_tuple_of_floats(self):
        latlon = self.method(self.coordinates)
        assert latlon == self.coordinates_str

    def test_string(self):
        latlon = self.method(self.coordinates_str)
        assert latlon == self.coordinates_str

    def test_string_is_trimmed(self):
        coordinates_str_spaces = "  %s  ,  %s  " % self.coordinates
        latlon = self.method(coordinates_str_spaces)
        assert latlon == self.coordinates_str

    def test_output_format_is_respected(self):
        expected = "  %s  %s  " % self.coordinates[::-1]
        lonlat = self.method(self.coordinates_str, "  %(lon)s  %(lat)s  ")
        assert lonlat == expected

    def test_address(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            latlon = self.method(self.coordinates_address)
            assert 1 == len(w)

        assert latlon == self.coordinates_address


class GeocoderFormatBoundingBoxTestCase(unittest.TestCase):

    def setUp(self):
        self.method = Geocoder._format_bounding_box

    def test_string_raises(self):
        with pytest.raises(GeocoderQueryError):
            self.method("5,5,5,5")

    def test_list_of_1_raises(self):
        with pytest.raises(GeocoderQueryError):
            self.method([5])

    # TODO maybe raise for `[5, 5]` too?

    def test_list_of_3_raises(self):
        with pytest.raises(GeocoderQueryError):
            self.method([5, 5, 5])

    def test_list_of_4_raises(self):
        with pytest.raises(GeocoderQueryError):
            self.method([5, 5, 5, 5])

    def test_list_of_5_raises(self):
        with pytest.raises(GeocoderQueryError):
            self.method([5, 5, 5, 5, 5])

    def test_points(self):
        bbox = self.method([Point(50, 160), Point(30, 170)])
        assert bbox == "30.0,160.0,50.0,170.0"

    def test_lists(self):
        bbox = self.method([[50, 160], [30, 170]])
        assert bbox == "30.0,160.0,50.0,170.0"
        bbox = self.method([["50", "160"], ["30", "170"]])
        assert bbox == "30.0,160.0,50.0,170.0"

    def test_strings(self):
        bbox = self.method(["50, 160", "30,170"])
        assert bbox == "30.0,160.0,50.0,170.0"

    def test_output_format(self):
        bbox = self.method([Point(50, 160), Point(30, 170)],
                           " %(lon2)s|%(lat2)s -- %(lat1)s|%(lon1)s ")
        assert bbox == " 170.0|50.0 -- 30.0|160.0 "
