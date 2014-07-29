
import unittest

from geopy.geocoders import MapQuest
from test.geocoders.util import GeocoderTestBase, CommonTestMixin, env


@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['MAPQUEST_KEY'] is not None,
    "No MAPQUEST_KEY env variable set"
)
class MapQuestTestCase(GeocoderTestBase, CommonTestMixin):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = MapQuest(
            env['MAPQUEST_KEY'],
            scheme='http',
            timeout=3
        )
        cls.delta = 0.04
