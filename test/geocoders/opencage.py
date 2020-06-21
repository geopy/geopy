import unittest

from geopy.geocoders import OpenCage
from test.geocoders.util import GeocoderTestBase, env


class OpenCageTestCaseUnitTest(GeocoderTestBase):

    def test_user_agent_custom(self):
        geocoder = OpenCage(
            api_key='DUMMYKEY1234',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'


@unittest.skipUnless(
    bool(env.get('OPENCAGE_KEY')),
    "No OPENCAGE_KEY env variables set"
)
class OpenCageTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = OpenCage(
            api_key=env['OPENCAGE_KEY'],
            timeout=10,
        )

    def test_geocode(self):
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        self.geocode_run(
            {"query": "\u6545\u5bab"},
            {"latitude": 39.916, "longitude": 116.390},
        )

    def test_geocode_empty_result(self):
        self.geocode_run(
            {"query": "xqj37"},
            {},
            expect_failure=True
        )

    def test_bounds(self):
        self.geocode_run(
            {"query": "moscow",  # Idaho USA
             "bounds": [[50.1, -130.1], [44.1, -100.9]]},
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )

    def test_country_str(self):
        self.geocode_run(
            {"query": "kazan",
             "country": 'tr'},
            {"latitude": 40.2317, "longitude": 32.6839},
        )

    def test_country_list(self):
        self.geocode_run(
            {"query": "kazan",
             "country": ['cn', 'tr']},
            {"latitude": 40.2317, "longitude": 32.6839},
        )
