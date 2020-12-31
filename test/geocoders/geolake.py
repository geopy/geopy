from geopy.geocoders import Geolake
from test.geocoders.util import BaseTestGeocoder, env


class TestUnitGeolake:

    def test_user_agent_custom(self):
        geocoder = Geolake(
            api_key='DUMMYKEY1234',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'


class TestGeolake(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return Geolake(
            api_key=env['GEOLAKE_KEY'],
            timeout=10,
            **kwargs
        )

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890344, "longitude": -87.623234, "address": "Chicago, US"},
        )

    async def test_geocode_country_codes_str(self):
        await self.geocode_run(
            {"query": "Toronto", "country_codes": "CA"},
            {"latitude": 43.72, "longitude": -79.47, "address": "Toronto, CA"},
        )
        await self.geocode_run(
            {"query": "Toronto", "country_codes": "RU"},
            {},
            expect_failure=True
        )

    async def test_geocode_country_codes_list(self):
        await self.geocode_run(
            {"query": "Toronto", "country_codes": ["CA", "RU"]},
            {"latitude": 43.72, "longitude": -79.47, "address": "Toronto, CA"},
        )
        await self.geocode_run(
            {"query": "Toronto", "country_codes": ["UA", "RU"]},
            {},
            expect_failure=True
        )

    async def test_geocode_structured(self):
        query = {
            "street": "north michigan ave",
            "houseNumber": "435",
            "city": "chicago",
            "state": "il",
            "zipcode": 60611,
            "country": "US"
        }
        await self.geocode_run(
            {"query": query},
            {"latitude": 41.890344, "longitude": -87.623234}
        )

    async def test_geocode_empty_result(self):
        await self.geocode_run(
            {"query": "xqj37"},
            {},
            expect_failure=True
        )

    async def test_geocode_missing_city_in_result(self):
        await self.geocode_run(
            {"query": "H1W 0B4"},
            {"latitude": 45.544952, "longitude": -73.546694, "address": "CA"}
        )
