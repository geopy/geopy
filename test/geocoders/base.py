import unittest
from contextlib import ExitStack
from unittest.mock import patch, sentinel

import pytest

import geopy.geocoders
import geopy.geocoders.base
from geopy.adapters import BaseAsyncAdapter, BaseSyncAdapter
from geopy.exc import GeocoderNotFound, GeocoderQueryError
from geopy.geocoders import GoogleV3, get_geocoder_for_service
from geopy.geocoders.base import Geocoder, _synchronized
from geopy.point import Point


class DummySyncAdapter(BaseSyncAdapter):
    def get_json(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def get_text(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError


class DummyAsyncAdapter(BaseAsyncAdapter):
    async def get_json(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    async def get_text(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError


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
        adapter = DummySyncAdapter(proxies=None, ssl_context=None)

        geocoder = Geocoder(
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=lambda **kw: adapter,
        )
        for attr in ('scheme', 'timeout', 'proxies', 'ssl_context'):
            assert locals()[attr] == getattr(geocoder, attr)
        assert user_agent == geocoder.headers['User-Agent']
        assert adapter is geocoder.adapter

    @patch.object(geopy.geocoders.options, 'default_adapter_factory',
                  DummySyncAdapter)
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
        assert DummySyncAdapter is type(geocoder.adapter)  # noqa

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

        g = Geocoder(adapter_factory=DummySyncAdapter)
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
                patch.object(
                    geopy.geocoders.base.options,
                    'default_adapter_factory',
                    return_value=DummySyncAdapter(proxies=None, ssl_context=None),
                )
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

    def test_near_zero(self):
        latlon = self.method(Point(50.0, -1.0e-5))
        assert latlon == "50.0,-0.0000100"


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


@pytest.mark.parametrize("adapter_factory", [DummySyncAdapter, DummyAsyncAdapter])
async def test_synchronize_decorator_sync_simple(adapter_factory):
    geocoder = Geocoder(adapter_factory=adapter_factory)
    calls = []

    @_synchronized
    def f(self, one, *, two):
        calls.append((one, two))
        return 42

    res = f(geocoder, 1, two=2)
    if adapter_factory is DummyAsyncAdapter:
        res = await res
    assert 42 == res
    assert calls == [(1, 2)]


async def test_synchronize_decorator_async_simple():
    geocoder = Geocoder(adapter_factory=DummyAsyncAdapter)
    calls = []

    @_synchronized
    def f(self, one, *, two):
        async def coro():
            calls.append((one, two))
            return 42
        return coro()

    assert 42 == await f(geocoder, 1, two=2)
    assert calls == [(1, 2)]


@pytest.mark.parametrize("adapter_factory", [DummySyncAdapter, DummyAsyncAdapter])
async def test_synchronize_decorator_sync_exception(adapter_factory):
    geocoder = Geocoder(adapter_factory=adapter_factory)

    @_synchronized
    def f(self, one, *, two):
        raise RuntimeError("test")

    with pytest.raises(RuntimeError):
        res = f(geocoder, 1, two=2)
        if adapter_factory is DummyAsyncAdapter:
            await res


async def test_synchronize_decorator_async_exception():
    geocoder = Geocoder(adapter_factory=DummyAsyncAdapter)

    @_synchronized
    def f(self, one, *, two):
        async def coro():
            raise RuntimeError("test")
        return coro()

    with pytest.raises(RuntimeError):
        await f(geocoder, 1, two=2)


@pytest.mark.parametrize("adapter_factory", [DummySyncAdapter, DummyAsyncAdapter])
async def test_synchronize_decorator_sync_reentrance(adapter_factory):
    calls = []

    class DummyGeocoder(Geocoder):
        @_synchronized
        def f(self, i=0):
            calls.append(i)
            if len(calls) < 5:
                return self.f(i + 1)
            return 42

    geocoder = DummyGeocoder(adapter_factory=adapter_factory)

    res = geocoder.f()
    if adapter_factory is DummyAsyncAdapter:
        res = await res
    assert 42 == res
    assert calls == list(range(5))


async def test_synchronize_decorator_async_reentrance():
    calls = []

    class DummyGeocoder(Geocoder):
        @_synchronized
        def f(self, i=0):
            async def coro():
                calls.append(i)
                if len(calls) < 5:
                    return await self.f(i + 1)
                return 42
            return coro()

    geocoder = DummyGeocoder(adapter_factory=DummyAsyncAdapter)

    assert 42 == await geocoder.f()
    assert calls == list(range(5))
