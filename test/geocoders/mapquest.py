import unittest

from geopy.compat import u
from geopy.geocoders import MapBox
from geopy.point import Point
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(
    bool(env.get('MAPQUEST_KEY')),
    "No MAPQUEST_KEY env variable set"
)
class MapBoxTestCase(GeocoderTestBase):
    @classmethod
    def setUpClass(cls):
        cls.geocoder = MapBox(api_key=env['MAPQUEST_KEY'], timeout=3)

    def test_geocode(self):
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.89036, "longitude": -87.624043},
        )

    def test_unicode_name(self):
        self.geocode_run(
            {"query": u("\u6545\u5bab")},
            {"latitude": 25.0968, "longitude": 121.54714},
        )

    def test_reverse(self):
        new_york_point = Point(40.75376406311989, -73.98489005863667)
        location = self.reverse_run(
            {"query": new_york_point, "exactly_one": True},
            {"latitude": 40.7537640, "longitude": -73.98489, "delta": 1},
        )
        self.assertIn("New York", location.address)

    def test_zero_results(self):
        self.geocode_run(
            {"query": ''},
            {},
            expect_failure=True,
        )

    def test_geocode_bbox(self):
        self.geocode_run(
            {
                "query": "435 north michigan ave, chicago il 60611 usa",
                "bbox": [Point(35.227672, -103.271484),
                         Point(48.603858, -74.399414)]
            },
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_geocode_raw(self):
        result = self.geocode_run({"query": "New York"}, {})
        self.assertTrue(isinstance(result.raw, dict))
        self.assertEqual(result.raw['latLng'], {'lat': 40.713054, 'lng': -74.007228})

    def test_geocode_exactly_one_true(self):
        list_result = self.geocode_run({"query": "New York", "exactly_one": False}, {})
        self.assertTrue(isinstance(list_result, list))
