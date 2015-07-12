
import unittest2 as unittest

from geopy.geocoders import LiveAddress
from geopy.exc import ConfigurationError, GeocoderAuthenticationFailure
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless( # pylint: disable=R0904,C0111
    'LIVESTREETS_AUTH_ID' in env and 'LIVESTREETS_AUTH_TOKEN' in env,
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
        try:
            self.geocode_run(
                {"query": "435 north michigan ave, chicago il 60611 usa"},
                {"latitude": 41.890, "longitude": -87.624},
            )
        except GeocoderAuthenticationFailure:
            raise unittest.SkipTest(
                "Non-geopy/geopy branches fail on this in CI due to an "
                "encrypted keys issue"  # TODO
            )

    def test_http_error(self):
        """
        LiveAddress() with scheme=http is a ConfigurationError
        """
        with self.assertRaises(ConfigurationError):
            LiveAddress(
                auth_id=env['LIVESTREETS_AUTH_ID'],
                auth_token=env['LIVESTREETS_AUTH_TOKEN'],
                scheme='http',
            )
