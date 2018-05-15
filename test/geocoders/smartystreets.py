import unittest
from mock import patch

import geopy.geocoders
from geopy.geocoders import LiveAddress
from geopy.exc import ConfigurationError
from test.geocoders.util import GeocoderTestBase, env


class LiveAddressTestCaseUnitTest(GeocoderTestBase):
    dummy_id = 'DUMMY12345'
    dummy_token = 'DUMMY67890'

    def test_user_agent_custom(self):
        geocoder = LiveAddress(
            auth_id=self.dummy_id,
            auth_token=self.dummy_token,
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_http_scheme_is_disallowed(self):
        with self.assertRaises(ConfigurationError):
            LiveAddress(
                auth_id=self.dummy_id,
                auth_token=self.dummy_token,
                scheme='http',
            )

    @patch.object(geopy.geocoders.options, 'default_scheme', 'http')
    def test_default_scheme_is_ignored(self):
        geocoder = LiveAddress(auth_id=self.dummy_id, auth_token=self.dummy_token)
        self.assertEqual(geocoder.scheme, 'https')
        geocoder = LiveAddress(auth_id=self.dummy_id, auth_token=self.dummy_token,
                               scheme=None)
        self.assertEqual(geocoder.scheme, 'https')


@unittest.skipUnless(
    env.get('LIVESTREETS_AUTH_ID') and env.get('LIVESTREETS_AUTH_TOKEN'),
    "No LIVESTREETS_AUTH_ID AND LIVESTREETS_AUTH_TOKEN env variables set"
)
class LiveAddressTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = LiveAddress(
            auth_id=env['LIVESTREETS_AUTH_ID'],
            auth_token=env['LIVESTREETS_AUTH_TOKEN'],
        )
        cls.delta = 0.04

    def test_geocode(self):
        """
        LiveAddress.geocode
        """
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )
