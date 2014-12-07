
import unittest

from geopy.compat import u
from geopy.point import Point
from geopy.geocoders import MapQuest
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(  # pylint: disable=R0904,C0111
    bool(env.get('MAPQUEST_KEY')),
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
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        """
        MapQuest.geocode unicode
        """
        self.geocode_run(
            {"query": u("\u6545\u5bab")},
            {"latitude": 39.916, "longitude": 116.390},
        )

    def test_reverse_point(self):
        """
        MapQuest.reverse using point
        """
        self.reverse_run(
            {"query": Point(40.753898, -73.985071)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )
