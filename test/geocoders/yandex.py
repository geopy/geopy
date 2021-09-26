import pytest

from geopy.exc import GeocoderInsufficientPrivileges
from geopy.geocoders import Yandex
from test.geocoders.util import BaseTestGeocoder, env


class TestYandex(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return Yandex(api_key=env['YANDEX_KEY'], **kwargs)

    async def test_user_agent_custom(self):
        geocoder = Yandex(
            api_key='mock',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "площадь Ленина Донецк"},
            {"latitude": 48.002104, "longitude": 37.805186},
        )

    async def test_failure_with_invalid_api_key(self):
        async with self.inject_geocoder(Yandex(api_key='bad key')):
            with pytest.raises(GeocoderInsufficientPrivileges):
                await self.geocode_run(
                    {"query": "площадь Ленина Донецк"},
                    {}
                )

    async def test_reverse(self):
        await self.reverse_run(
            {"query": "40.75376406311989, -73.98489005863667"},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    async def test_geocode_lang(self):
        await self.geocode_run(
            {"query": "площа Леніна Донецьк", "lang": "uk_UA"},
            {"address": "площа Леніна, Донецьк, Україна",
             "latitude": 48.002104, "longitude": 37.805186},
        )

    async def test_reverse_kind(self):
        await self.reverse_run(
            {"query": (55.743659, 37.408055), "kind": "locality"},
            {"address": "Москва, Россия"}
        )

    async def test_reverse_lang(self):
        await self.reverse_run(
            {"query": (55.743659, 37.408055), "kind": "locality",
             "lang": "uk_UA"},
            {"address": "Москва, Росія"}
        )
