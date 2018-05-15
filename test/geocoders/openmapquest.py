
from geopy.compat import u
from geopy.geocoders import OpenMapQuest
from test.geocoders.util import GeocoderTestBase, env
import unittest


class OpenMapQuestNoNetTestCase(GeocoderTestBase):

    def test_user_agent_custom(self):
        geocoder = OpenMapQuest(
            api_key='DUMMYKEY1234',
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')


@unittest.skipUnless(
    bool(env.get('OPENMAPQUEST_APIKEY')),
    "No OPENMAPQUEST_APIKEY env variable set"
)
class OpenMapQuestTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        # setUpClass is still called even if test is skipped.
        # OpenMapQuest raises ConfigurationError when api_key is empty,
        # so don't try to create the instance when api_key is empty.
        if env.get('OPENMAPQUEST_APIKEY'):
            cls.geocoder = OpenMapQuest(scheme='http', timeout=3,
                                        api_key=env['OPENMAPQUEST_APIKEY'])
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
