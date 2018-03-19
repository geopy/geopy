
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


@unittest.skipUnless(  # pylint: disable=R0904,C0111
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
        res = self._make_request(
            self.geocoder.geocode,
            "435 north michigan ave, chicago il 60611 usa",
        )
        if res is None:
            unittest.SkipTest("Bing sometimes returns no result")
        else:
            self.assertAlmostEqual(res.latitude, 41.890, delta=self.delta)
            self.assertAlmostEqual(res.longitude, -87.624, delta=self.delta)

    def test_unicode_name(self):
        """
        Bing.geocode unicode
        """
        res = self._make_request(
            self.geocoder.geocode,
            u("\u6545\u5bab"),
        )
        if res is None:
            unittest.SkipTest("Bing sometimes returns no result")
        else:
            self.assertAlmostEqual(res.latitude, 39.916, delta=self.delta)
            self.assertAlmostEqual(res.longitude, 116.390, delta=self.delta)

    def test_reverse_point(self):
        """
        Bing.reverse using point
        """
        res = self._make_request(
            self.geocoder.reverse,
            Point(40.753898, -73.985071)
        )
        if res is None:
            unittest.SkipTest("Bing sometimes returns no result")
        else:
            self.assertAlmostEqual(res.latitude, 40.753, delta=self.delta)
            self.assertAlmostEqual(res.longitude, -73.984, delta=self.delta)

    def test_reverse_with_culture_de(self):
        """
        Bing.reverse using point and culture parameter to get a non english response
        """
        res = self._make_request(
            self.geocoder.reverse,
            Point(40.753898, -73.985071),
            culture="DE"
        )
        if res is None:
            unittest.SkipTest("Bing sometimes returns no result")
        else:
            self.assertIn("Vereinigte Staaten von Amerika", res.address)

    def test_reverse_with_culture_en(self):
        """
        Bing.reverse using point and culture parameter to get an english response
        """
        res = self._make_request(
            self.geocoder.reverse,
            Point(40.753898, -73.985071),
            culture="EN"
        )
        if res is None:
            unittest.SkipTest("Bing sometimes returns no result")
        else:
            self.assertIn("United States", res.address)

    def test_reverse_with_include_country_code(self):
        """
        Bing.reverse using point and include country-code in the response
        """
        res = self._make_request(
            self.geocoder.reverse,
            Point(40.753898, -73.985071),
            include_country_code=True
        )
        if res is None:
            unittest.SkipTest("Bing sometimes returns no result")
        else:
            self.assertEqual(res.raw["address"].get("countryRegionIso2", 'missing'), 'US')

    def test_user_location(self):
        """
        Bing.geocode using `user_location`
        """
        pensylvania = "20 Main St, Blairstown, NJ 07825, United States"
        colorado = "20 Main St, Longmont, CO 80501, United States"

        pennsylvania_bias = (40.922351, -75.096562)
        colorado_bias = (39.914231, -105.070104)
        for each in (
                (pensylvania, pennsylvania_bias),
                (colorado, colorado_bias)
            ):
            res = self._make_request(
                self.geocoder.geocode,
                "20 Main Street",
                user_location=Point(each[1]),
            )
            if res is None:
                unittest.SkipTest("Bing sometimes returns no result")
            else:
                self.assertEqual(res[0], each[0])

    def test_optional_params(self):
        """
        Bing.geocode using optional params
        """
        address_string = "Badeniho 1, Prague, Czech Republic"

        res = self._make_request(
            self.geocoder.geocode,
            query=address_string,
            culture='cs',
            include_neighborhood=True,
            include_country_code=True
        )
        if res is None:
            unittest.SkipTest("Bing sometimes returns no result")
        else:
            address = res.raw['address']

        self.assertEqual(address['neighborhood'], "Praha 6")
        self.assertEqual(address['countryRegionIso2'], "CZ")

    def test_structured_query(self):
        """
        Bing.geocode using structured query
        """
        address_dict = {'postalCode': '80020', 'countryRegion': 'United States'}
        res = self._make_request(
            self.geocoder.geocode,
            query=address_dict
        )
        if res is None:
            unittest.SkipTest("Bing sometimes returns no result")
        else:
            address = res.raw['address']
            self.assertEqual(address['locality'], "Broomfield")
