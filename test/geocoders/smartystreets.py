
import unittest

from geopy.geocoders import LiveAddress
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(  # pylint: disable=R0904,C0111
    bool(env.get('LIVESTREETS_AUTH_KEY')),
    "No LIVESTREETS_AUTH_KEY env variable set"
)
class LiveAddressTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = LiveAddress(
            auth_token=env['LIVESTREETS_AUTH_KEY'],
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
