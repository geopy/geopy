
import unittest

from geopy.geocoders import Geoclient
from test.geocoders.util import GeocoderTestBase, env

class GeoclientTestCaseUnitTest(GeocoderTestBase):

    def test_user_agent_custom(self):
        geocoder = Geoclient(
            app_id='DUMMY12345',
            app_key='DUMMY67890',
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')


@unittest.skipUnless(
    'GEOCLIENT_APP_ID' in env and 'GEOCLIENT_APP_KEY' in env,
    "No GEOCLIENT_APP_ID AND GEOCLIENT_APP_KEY env variables set"
)
class GeoclientTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Geoclient(
            app_id=env['GEOCLIENT_APP_ID'],
            app_key=env['GEOCLIENT_APP_KEY'],
        )
        cls.delta = 0.04

    def test_geocode(self):
        """
        Geoclient.geocode
        """
        self.geocode_run(
            {"query": "85 Fifth Ave, Manhattan, NY"},
            {"latitude": 40.737415391891616, "longitude": -73.9925809709183},  
        )

