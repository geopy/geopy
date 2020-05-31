import unittest

from geopy.geocoders import Geolake
from test.geocoders.util import GeocoderTestBase, env


class GeolakeTestCaseUnitTest(GeocoderTestBase):

    def test_user_agent_custom(self):
        geocoder = Geolake(
            api_key='DUMMYKEY1234',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'


@unittest.skipUnless(
    bool(env.get('GEOLAKE_KEY')),
    "No GEOLAKE_KEY env variables set"
)
class GeolakeTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Geolake(
            api_key=env['GEOLAKE_KEY'],
            timeout=10,
        )

    def test_geocode(self):
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890344, "longitude": -87.623234, "address": "Chicago, US"},
        )

    def test_geocode_country_codes_str(self):
        self.geocode_run(
            {"query": "Toronto", "country_codes": "US"},
            {"latitude": 40.46, "longitude": -80.6, "address": "Toronto, US"},
        )

    def test_geocode_country_codes_list(self):
        self.geocode_run(
            {"query": "Toronto", "country_codes": ["CN", "US"]},
            {"latitude": 40.46, "longitude": -80.6, "address": "Toronto, US"},
        )

    def test_geocode_structured(self):
        query = {
            "street": "north michigan ave",
            "houseNumber": "435",
            "city": "chicago",
            "state": "il",
            "zipcode": 60611,
            "country": "US"
        }
        self.geocode_run(
            {"query": query},
            {"latitude": 41.890344, "longitude": -87.623234}
        )

    def test_geocode_empty_result(self):
        self.geocode_run(
            {"query": "xqj37"},
            {},
            expect_failure=True
        )

    def test_geocode_missing_city_in_result(self):
        self.geocode_run(
            {"query": "H1W 0B4"},
            {"latitude": 45.544952, "longitude": -73.546694, "address": "CA"}
        )
