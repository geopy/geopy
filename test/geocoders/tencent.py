import pytest

from geopy.exc import GeocoderAuthenticationFailure, GeocoderQueryError
from geopy.geocoders import Tencent
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


class TestTencent(BaseTestGeocoder):
    @classmethod
    def make_geocoder(cls, **kwargs):
        return Tencent(api_key=env["Tencent_KEY"], timeout=3, **kwargs)

    async def test_illegal_ak(self):
        async with self.inject_geocoder(Tencent(api_key="DUMMYKEY1234")):
            with pytest.raises(GeocoderQueryError) as exc_info:
                await self.geocode_run({"query": "tencent"}, None)
            assert str(exc_info.value) == "KEY illegal or not exist key格式错误."

    async def test_invalid_ak(self):
        async with self.inject_geocoder(
            Tencent(api_key="00000-00000-00000-00000-00000-00000")
        ):
            with pytest.raises(GeocoderAuthenticationFailure) as exc_info:
                await self.geocode_run({"query": "tencent"}, None)
            assert str(exc_info.value) == "Invalid KEY 无效的KEY."

    async def test_geocode_address(self):
        await self.geocode_run(
            {
                "query": (
                    "\u5317\u4eac\u5e02\u6d77\u6dc0\u533a\u5f69\u548c\u574a"
                    "\u8def\u6d77\u6dc0\u897f\u5927\u8857\u0037\u0034\u53f7"
                )
            },
            {"latitude": 39.982915, "longitude": 116.307015},
        )

    async def test_reverse_point(self):
        await self.reverse_run(
            {"query": Point(39.984154, 116.307490)},
            {"latitude": 39.984154, "longitude": 116.30749},
        )
