from geopy.geocoders import Bing
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


class TestUnitBing:

    def test_user_agent_custom(self):
        geocoder = Bing(
            api_key='DUMMYKEY1234',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'


class TestBing(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return Bing(
            api_key=env['BING_KEY'],
            **kwargs
        )

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    async def test_reverse_point(self):
        await self.reverse_run(
            {"query": Point(40.753898, -73.985071)},
            {"latitude": 40.753, "longitude": -73.984},
        )

    async def test_reverse_with_culture_de(self):
        res = await self.reverse_run(
            {"query": Point(40.753898, -73.985071), "culture": "DE"},
            {},
        )
        assert "Vereinigte Staaten von Amerika" in res.address

    async def test_reverse_with_culture_en(self):
        res = await self.reverse_run(
            {"query": Point(40.753898, -73.985071), "culture": "EN"},
            {},
        )
        assert "United States" in res.address

    async def test_reverse_with_include_country_code(self):
        res = await self.reverse_run(
            {"query": Point(40.753898, -73.985071),
             "include_country_code": True},
            {},
        )
        assert res.raw["address"].get("countryRegionIso2", 'missing') == 'US'

    async def test_user_location(self):
        await self.geocode_run(
            {"query": "Kings Road", "user_location": Point(51.5043, -0.1260)},
            {"latitude": 51.4615, "longitude": -0.2926, "delta": 0.5},
        )
        await self.geocode_run(
            {"query": "Kings Road"},
            {"latitude": 53.3356, "longitude": -2.2464, "delta": 0.5},
        )

    async def test_optional_params(self):
        res = await self.geocode_run(
            {"query": "Ballard, WA",
             "include_neighborhood": True,
             "include_country_code": True},
            {},
        )
        address = res.raw['address']
        assert address['neighborhood'] == "Ballard"
        assert address['countryRegionIso2'] == "US"

    async def test_structured_query(self):
        res = await self.geocode_run(
            {"query": {'postalCode': '80020', 'countryRegion': 'United States'}},
            {},
        )
        address = res.raw['address']
        assert address['locality'] == "Broomfield"
