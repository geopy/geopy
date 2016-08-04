
from geopy.compat import u
from geopy.geocoders import OpenMapQuest
from test.geocoders.util import GeocoderTestBase, env
import unittest


class OpenMapQuestNoNetTestCase(GeocoderTestBase):  # pylint: disable=R0904,C0111

    def test_user_agent_custom(self):
        geocoder = OpenMapQuest(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')


@unittest.skipUnless(  # pylint: disable=R0904,C0111
    bool(env.get('OPENMAPQUEST_APIKEY')),
    "No OPENMAPQUEST_APIKEY env variable set"
)
class OpenMapQuestTestCase(GeocoderTestBase):  # pylint: disable=R0904,C0111

    @classmethod
    def setUpClass(cls):
        cls.geocoder = OpenMapQuest(scheme='http', timeout=3,
                                    api_key=env.get('OPENMAPQUEST_APIKEY'))
        cls.delta = 0.04

    def test_geocode(self):
        """
        OpenMapQuest.geocode
        """
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        """
        OpenMapQuest.geocode unicode
        """
        self.geocode_run(
            {"query": u("\u6545\u5bab")},
            {"latitude": 39.916, "longitude": 116.390},
        )
