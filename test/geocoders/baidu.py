import pytest

from geopy.exc import GeocoderAuthenticationFailure
from geopy.geocoders import Baidu, BaiduV3
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


class TestUnitBaidu(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return Baidu(
            api_key='DUMMYKEY1234',
            user_agent='my_user_agent/1.0',
            **kwargs
        )

    async def test_user_agent_custom(self):
        assert self.geocoder.headers['User-Agent'] == 'my_user_agent/1.0'


class BaseTestBaidu(BaseTestGeocoder):

    async def test_basic_address(self):
        await self.geocode_run(
            {"query": (
                "\u5317\u4eac\u5e02\u6d77\u6dc0\u533a"
                "\u4e2d\u5173\u6751\u5927\u885727\u53f7"
            )},
            {"latitude": 39.983615544507, "longitude": 116.32295155093},
        )

    async def test_reverse_point(self):
        await self.reverse_run(
            {"query": Point(39.983615544507, 116.32295155093)},
            {"latitude": 39.983615544507, "longitude": 116.32295155093},
        )
        await self.reverse_run(
            {"query": Point(39.983615544507, 116.32295155093), "exactly_one": False},
            {"latitude": 39.983615544507, "longitude": 116.32295155093},
        )


class TestBaidu(BaseTestBaidu):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return Baidu(
            api_key=env['BAIDU_KEY'],
            timeout=3,
            **kwargs,
        )

    async def test_invalid_ak(self):
        async with self.inject_geocoder(Baidu(api_key='DUMMYKEY1234')):
            with pytest.raises(GeocoderAuthenticationFailure) as exc_info:
                await self.geocode_run({"query": "baidu"}, None)
            assert str(exc_info.value) == 'Invalid AK'


class TestBaiduSK(BaseTestBaidu):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return Baidu(
            api_key=env['BAIDU_KEY_REQUIRES_SK'],
            security_key=env['BAIDU_SEC_KEY'],
            timeout=3,
            **kwargs,
        )

    async def test_sn_with_peculiar_chars(self):
        await self.geocode_run(
            {"query": (
                "\u5317\u4eac\u5e02\u6d77\u6dc0\u533a"
                "\u4e2d\u5173\u6751\u5927\u885727\u53f7"
                " ' & = , ? %"
            )},
            {"latitude": 39.983615544507, "longitude": 116.32295155093},
        )


class TestBaiduV3(TestBaidu):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return BaiduV3(
            api_key=env['BAIDU_V3_KEY'],
            timeout=3,
            **kwargs,
        )


class TestBaiduV3SK(TestBaiduSK):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return BaiduV3(
            api_key=env['BAIDU_V3_KEY_REQUIRES_SK'],
            security_key=env['BAIDU_V3_SEC_KEY'],
            timeout=3,
            **kwargs,
        )
