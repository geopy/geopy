
import unittest

from geopy.compat import u
from geopy.geocoders import OpenCage
from test.geocoders.util import GeocoderTestBase, env


class OpenCageTestCaseUnitTest(GeocoderTestBase):

    def test_user_agent_custom(self):
        geocoder = OpenCage(
            api_key='DUMMYKEY1234',
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')


@unittest.skipUnless(  # pylint: disable=R0904,C0111
    bool(env.get('OPENCAGE_KEY')),
    "No OPENCAGE_KEY env variables set"
)
class OpenCageTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = OpenCage(
            api_key=env['OPENCAGE_KEY'],
            timeout=20,
        )
        cls.delta_exact = 0.2

    def test_geocode(self):
        """
        OpenCage.geocode
        """
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        """
        OpenCage.geocode unicode
        """
        self.geocode_run(
            {"query": u("\u6545\u5bab")},
            {"latitude": 39.916, "longitude": 116.390},
        )

    def test_geocode_empty_result(self):
        """
        Empty OpenCage.geocode results should be graciously handled.
        """
        self.geocode_run(
            {
                "query": "xqj37",
            },
            {},
            expect_failure=True
        )
