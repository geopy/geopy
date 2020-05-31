import unittest

from geopy.compat import u
from geopy.geocoders import Bing
from geopy.point import Point
from test.geocoders.util import GeocoderTestBase, env


class BingTestCaseUnitTest(GeocoderTestBase):

    def test_user_agent_custom(self):
        geocoder = Bing(
            api_key='DUMMYKEY1234',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'


@unittest.skipUnless(
    bool(env.get('BING_KEY')),
    "No BING_KEY env variable set"
)
class BingTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Bing(
            api_key=env['BING_KEY']
        )

    def test_geocode(self):
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        self.geocode_run(
            {"query": u("\u043c\u043e\u0441\u043a\u0432\u0430")},
            {"latitude": 55.756, "longitude": 37.615},
        )

    def test_reverse_point(self):
        self.reverse_run(
            {"query": Point(40.753898, -73.985071)},
            {"latitude": 40.753, "longitude": -73.984},
        )

    def test_reverse_with_culture_de(self):
        res = self.reverse_run(
            {"query": Point(40.753898, -73.985071), "culture": "DE"},
            {},
        )
        assert "Vereinigte Staaten von Amerika" in res.address

    def test_reverse_with_culture_en(self):
        res = self.reverse_run(
            {"query": Point(40.753898, -73.985071), "culture": "EN"},
            {},
        )
        assert "United States" in res.address

    def test_reverse_with_include_country_code(self):
        res = self.reverse_run(
            {"query": Point(40.753898, -73.985071),
             "include_country_code": True},
            {},
        )
        assert res.raw["address"].get("countryRegionIso2", 'missing') == 'US'

    def test_user_location(self):
        pennsylvania = (40.98327, -74.96064)
        colorado = (40.1602849999851, -105.102491162672)

        pennsylvania_bias = (40.922351, -75.096562)
        colorado_bias = (39.914231, -105.070104)
        for expected, bias in ((pennsylvania, pennsylvania_bias),
                               (colorado, colorado_bias)):
            try:
                self.geocode_run(
                    {"query": "20 Main Street", "user_location": Point(bias)},
                    {"latitude": expected[0], "longitude": expected[1]},
                )
            except AssertionError as e:
                self.skipTest("Bing ignored user_location: %s" % str(e))

    def test_optional_params(self):
        res = self.geocode_run(
            {"query": "Badeniho 1, Prague, Czech Republic",
             "culture": 'cs',
             "include_neighborhood": True,
             "include_country_code": True},
            {},
        )
        address = res.raw['address']
        assert address['neighborhood'] == "Praha 6"
        assert address['countryRegionIso2'] == "CZ"

    def test_structured_query(self):
        res = self.geocode_run(
            {"query": {'postalCode': '80020', 'countryRegion': 'United States'}},
            {},
        )
        address = res.raw['address']
        assert address['locality'] == "Broomfield"
