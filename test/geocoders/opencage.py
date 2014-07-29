
import unittest

from geopy.geocoders import OpenCage
from test.geocoders.util import GeocoderTestBase, CommonTestMixin, env


@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['OPENCAGE_KEY'] is not None,
    "No OPENCAGE_KEY env variables set"
)
class OpenCageTestCase(GeocoderTestBase, CommonTestMixin):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = OpenCage(
            api_key=env['OPENCAGE_KEY'],
            timeout=20,
        )
        cls.delta_exact = 0.2
