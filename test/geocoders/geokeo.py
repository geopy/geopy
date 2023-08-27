import pytest

from geopy.geocoders import Geokeo
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


class TestUnitGeokeo:

    def test_user_agent_custom(self):
        geocoder = Geokeo(
            api_key='DUMMYKEY1234',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'


class TestGeokeo(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return Geokeo(
            api_key=env['GEOKEY_KEY'],
            timeout=10,
            **kwargs
        )

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "empire state building"},
            {"latitude": 40.74843124430164, "longitude": -73.9856567114413},
        )

    async def test_geocode_country(self):
        await self.geocode_run(
            {"query": "moscow", "country": "us"},
            {"latitude": 46.730685699940594, "longitude": -116.99875169095164},
        )
        await self.geocode_run(
            {"query": "moscow", "country": "ru"},
            {"latitude": 55.75044609968516, "longitude": 37.6174943},
        )

    @pytest.mark.xfail(reason="invalid json is returned at the moment")
    async def test_geocode_empty_result(self):
        await self.geocode_run(
            {"query": "xqj37"},
            {},
            expect_failure=True
        )

    async def test_reverse(self):
        location = await self.reverse_run(
            {"query": Point(40.74843124430164, -73.9856567114413)},
            {"latitude": 40.74843124430164, "longitude": -73.9856567114413},
        )
        assert "Empire State Building" in location.address

    async def test_reverse_empty_result(self):
        await self.reverse_run(
            {"query": Point(0.05, -0.15)},
            {},
            expect_failure=True,
        )
