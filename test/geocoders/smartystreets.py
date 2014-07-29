
import unittest

from geopy.geocoders import LiveAddress
from test.geocoders.util import GeocoderTestBase, CommonTestMixin, env


@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['LIVESTREETS_AUTH_KEY'] is not None,
    "No LIVESTREETS_AUTH_KEY env variable set"
)
class LiveAddressTestCase(GeocoderTestBase, CommonTestMixin):
    def setUp(self):
        self.geocoder = LiveAddress(
            auth_token=env['LIVESTREETS_AUTH_KEY'],
            scheme='http'
        )
        self.delta = 0.04

