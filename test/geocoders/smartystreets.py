
import unittest

from geopy.geocoders import LiveAddress
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless( # pylint: disable=R0904,C0111
    (
        env['LIVESTREETS_AUTH_ID'] is not None and
        env['LIVESTREETS_AUTH_TOKEN'] is not None
    ),
    "No LIVESTREETS_AUTH_ID AND LIVESTREETS_AUTH_TOKEN env variables set"
)
class LiveAddressTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = LiveAddress(
            auth_id=env['LIVESTREETS_AUTH_ID'],
            auth_token=env['LIVESTREETS_AUTH_TOKEN'],
            scheme='http'
        )
        cls.delta = 0.04

    def test_geocode(self):
        """
        LiveAddress.geocode
        """
        self.geocode_run(
            {"query": u"435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )
