from pytz import timezone
import unittest

from geopy.compat import u
from geopy.point import Point
from geopy.geocoders import MapBox
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(
    bool(env.get('MAPBOX_KEY')),
    "No MAPBOX env variable set"
)
class MapBoxTestCase(GeocoderTestBase):
    @classmethod
    def setUpClass(cls):
        cls.geocoder = MapBox(api_key=env['MAPBOX_KEY'])
        cls.new_york_point = Point(40.75376406311989, -73.98489005863667)
        cls.america_new_york = timezone("America/New_York")

    def test_geocode(self):
        """
        MapBox.geocode
        """

        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        """
        MapBox.geocode unicode
        """
        self.geocode_run(
            {"query": u("\u6545\u5bab")},
            {"latitude": 39.916, "longitude": 116.390},
        )

    def test_reverse_string(self):
        """
        MapBox.reverse string
        """
        self.reverse_run(
            {"query": "40.75376406311989, -73.98489005863667", "exactly_one": True},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    def test_reverse_point(self):
        """
        MapBox.reverse Point
        """
        self.reverse_run(
            {"query": self.new_york_point, "exactly_one": True},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    def test_zero_results(self):
        """
        MapBox.geocode returns None for no result
        """
        self.geocode_run(
            {"query": 'asdfasdfasdf'},
            {},
            expect_failure=True,
        )

    def test_geocode_outside_bbox(self):
        self.geocode_run(
            {
                "query": "435 north michigan ave, chicago il 60611 usa",
                "bbox": [-118.604794, 34.172684, -118.500938, 34.236144]
            },
            {},
            expect_failure=True,
        )

    def test_geocode_bbox(self):
        self.geocode_run(
            {
                "query": "435 north michigan ave, chicago il 60611 usa",
                "bbox": [-103.271484, 35.227672, -74.399414, 48.603858]
            },
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_geocode_proximity(self):
        self.geocode_run(
            {"query": "200 queen street", "proximity": [45.3, -66.1]},
            {"latitude": -33.994267, "longitude": 138.881142},
        )
