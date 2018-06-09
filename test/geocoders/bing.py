
import unittest

from geopy.compat import u
from geopy.point import Point
from geopy.geocoders import Bing
from test.geocoders.util import GeocoderTestBase, env


class BingTestCaseUnitTest(GeocoderTestBase):

    def test_user_agent_custom(self):
        geocoder = Bing(
            api_key='DUMMYKEY1234',
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')


@unittest.skipUnless(
    bool(env.get('BING_KEY')),
    "No BING_KEY env variable set"
)
class BingTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Bing(
            format_string='%s',
            scheme='http',
            api_key=env['BING_KEY']
        )

    def test_geocode(self):
        """
        Bing.geocode
        """
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        """
        Bing.geocode unicode
        """
        self.geocode_run(
            {"query": u("\u043c\u043e\u0441\u043a\u0432\u0430")},
            {"latitude": 55.756, "longitude": 37.615},
        )

    def test_reverse_point(self):
        """
        Bing.reverse using point
        """
        self.reverse_run(
            {"query": Point(40.753898, -73.985071)},
            {"latitude": 40.753, "longitude": -73.984},
        )

    def test_reverse_with_culture_de(self):
        """
        Bing.reverse using point and culture parameter to get a non english response
        """
        res = self.reverse_run(
            {"query": Point(40.753898, -73.985071), "culture": "DE"},
            {},
        )
        self.assertIn("Vereinigte Staaten von Amerika", res.address)

    def test_reverse_with_culture_en(self):
        """
        Bing.reverse using point and culture parameter to get an english response
        """
        res = self.reverse_run(
            {"query": Point(40.753898, -73.985071), "culture": "EN"},
            {},
        )
        self.assertIn("United States", res.address)

    def test_reverse_with_include_country_code(self):
        """
        Bing.reverse using point and include country-code in the response
        """
        res = self.reverse_run(
            {"query": Point(40.753898, -73.985071),
             "include_country_code": True},
            {},
        )
        self.assertEqual(res.raw["address"].get("countryRegionIso2", 'missing'), 'US')

    def test_user_location(self):
        """
        Bing.geocode using `user_location`
        """
        pennsylvania = (40.98327, -74.96064)
        colorado = (40.1602849999851, -105.102491162672)

        pennsylvania_bias = (40.922351, -75.096562)
        colorado_bias = (39.914231, -105.070104)
        for expected, bias in ((pennsylvania, pennsylvania_bias),
                               (colorado, colorado_bias)):
            self.geocode_run(
                {"query": "20 Main Street", "user_location": Point(bias)},
                {"latitude": expected[0], "longitude": expected[1]},
            )

    def test_optional_params(self):
        """
        Bing.geocode using optional params
        """
        res = self.geocode_run(
            {"query": "Badeniho 1, Prague, Czech Republic",
             "culture": 'cs',
             "include_neighborhood": True,
             "include_country_code": True},
            {},
        )
        address = res.raw['address']
        self.assertEqual(address['neighborhood'], "Praha 6")
        self.assertEqual(address['countryRegionIso2'], "CZ")

    def test_structured_query(self):
        """
        Bing.geocode using structured query
        """
        res = self.geocode_run(
            {"query": {'postalCode': '80020', 'countryRegion': 'United States'}},
            {},
        )
        address = res.raw['address']
        self.assertEqual(address['locality'], "Broomfield")
