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
        moscow_idaho = (46.7323875, -117.0001651)
        moscow_idaho_bias = (46.7323875, -117.0001651)

        moscow_ru = (55.75582886, 37.61722183)
        moscow_ru_bias = (55.75582886, 37.61722183)
        for expected, bias in ((moscow_idaho, moscow_idaho_bias),
                               (moscow_ru, moscow_ru_bias)):
            await self.geocode_run(
                {"query": "moscow", "user_location": Point(bias)},
                {"latitude": expected[0], "longitude": expected[1], "delta": 3.0},
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
