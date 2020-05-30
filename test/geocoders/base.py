import unittest
from contextlib import ExitStack
from unittest.mock import patch, sentinel

import pytest

import geopy.geocoders
import geopy.geocoders.base
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
            adapter_factory=lambda **kw: sentinel.local_adapter,
        )
        for attr in ('scheme', 'timeout', 'proxies', 'ssl_context'):
            assert locals()[attr] == getattr(geocoder, attr)
        assert user_agent == geocoder.headers['User-Agent']
        assert sentinel.local_adapter is geocoder.adapter

    @patch.object(geopy.geocoders.options, 'default_adapter_factory',
                  lambda **kw: sentinel.default_adapter)
    def test_init_with_defaults(self):
        attr_to_option = {
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
        assert sentinel.default_adapter is geocoder.adapter

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

        with ExitStack() as stack:
            mock_get_json = stack.enter_context(patch.object(g.adapter, 'get_json'))

            g._call_geocoder(url, lambda res: res)
            args, kwargs = mock_get_json.call_args
            assert kwargs['timeout'] == 12

            g._call_geocoder(url, lambda res: res, timeout=7)
            args, kwargs = mock_get_json.call_args
            assert kwargs['timeout'] == 7

            g._call_geocoder(url, lambda res: res, timeout=None)
            args, kwargs = mock_get_json.call_args
            assert kwargs['timeout'] is None

    def test_ssl_context(self):
        with ExitStack() as stack:
            mock_adapter = stack.enter_context(
                patch.object(geopy.geocoders.base.options, 'default_adapter_factory')
            )

            for ssl_context in (None, sentinel.some_ssl_context):
                Geocoder(ssl_context=ssl_context)
                args, kwargs = mock_adapter.call_args
                assert kwargs['ssl_context'] is ssl_context


class GeocoderPointCoercionTestCase(unittest.TestCase):
    coordinates = (40.74113, -73.989656)
    coordinates_str = "40.74113,-73.989656"
    coordinates_address = "175 5th Avenue, NYC, USA"

    def setUp(self):
        self.method = Geocoder()._coerce_point_to_string

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
        with pytest.raises(ValueError):
            self.method(self.coordinates_address)


class GeocoderFormatBoundingBoxTestCase(unittest.TestCase):

    def setUp(self):
        self.method = Geocoder()._format_bounding_box

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
