
import unittest

from geopy.geocoders import MapQuest
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['MAPQUEST_KEY'] is not None,
    "No MAPQUEST_KEY env variable set"
)
class MapQuestTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = MapQuest(
            env['MAPQUEST_KEY'],
            scheme='http',
            timeout=3
        )
        cls.delta = 0.7

    def test_geocode(self):
        """
        MapQuest.geocode
        """
        self.geocode_run(
            {"query": u"435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        """
        MapQuest.geocode unicode
        """
        self.geocode_run(
            {"query": u"\u6545\u5bab"},
            {"latitude": 39.916, "longitude": 116.390},
        )


