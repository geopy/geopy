from geopy.geocoders import Ip2geo
from test.geocoders.util import BaseTestGeocoder, env


class TestIp2geo(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return Ip2geo(api_key=env['IP2GEO_KEY'], **kwargs)

    async def test_user_agent_custom(self):
        geocoder = self.make_geocoder(user_agent='my_user_agent/1.0')
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    async def test_geocode(self):
        location = await self.geocode_run(
            {"query": "134.201.250.155"},
            {"latitude": 34.0, "longitude": -118.2},
            skipIfParseError=True,
        )
        if location:
            assert location.address

    async def test_geocode_no_city(self):
        location = await self.geocode_run(
            {"query": "8.8.8.8"},
            {"latitude": 37.7, "longitude": -97.8},
            skipIfParseError=True,
        )
        if location:
            assert location.raw.get('ip') == '8.8.8.8'

    async def test_geocode_exactly_one_false(self):
        result = await self.geocode_run(
            {"query": "134.201.250.155", "exactly_one": False},
            {},
            skipIfParseError=True,
        )
        if result:
            assert isinstance(result, list)
            assert len(result) == 1
