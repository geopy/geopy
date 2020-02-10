# -*- coding: utf-8 -*-
import unittest

from geopy.compat import u
from geopy.geocoders import MapTiler
from geopy.location import Location
from geopy.point import Point
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(
    bool(env.get('MAPTILER_KEY')),
    "No MAPTILER_KEY env variable set"
)
class MapTilerTestCase(GeocoderTestBase):
    @classmethod
    def setUpClass(cls):
        cls.geocoder = MapTiler(api_key=env['MAPTILER_KEY'], timeout=3)

    def test_geocode(self):
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        self.geocode_run(
            {"query": u("Stadelhoferstrasse 8, 8001 Z\u00fcrich")},
            {"latitude": 47.36649, "longitude": 8.54855},
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
            {"query": 'asdfasdfasdf'},
            {},
            expect_failure=True,
        )

    def test_geocode_outside_bbox(self):
        self.geocode_run(
            {
                "query": "435 north michigan ave, chicago il 60611 usa",
                "bbox": [[34.172684, -118.604794],
                         [34.236144, -118.500938]]
            },
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

    def test_geocode_proximity(self):
        self.geocode_run(
            {"query": "200 queen street", "proximity": Point(45.3, -66.1)},
            {"latitude": 44.038901, "longitude": -64.73052, "delta": 0.1},
        )

    def test_reverse_language(self):
        zurich_point = Point(47.3723, 8.5422)
        location = self.reverse_run(
            {"query": zurich_point, "exactly_one": True, "language": "ja"},
            {"latitude": 47.3723, "longitude": 8.5422, "delta": 1},
        )
        self.assertIn("チューリッヒ", location.address)

    def test_geocode_language(self):
        location = self.geocode_run(
            {"query": "Zürich", "exactly_one": True, "language": "ja",
             "proximity": Point(47.3723, 8.5422)},
            {"latitude": 47.3723, "longitude": 8.5422, "delta": 1},
        )
        self.assertIn("チューリッヒ", location.address)

    def test_geocode_raw(self):
        result = self.geocode_run({"query": "New York"}, {})
        delta = 0.00001
        self.assertTrue(isinstance(result.raw, dict))
        self.assertAlmostEqual(-73.8784155, result.raw['center'][0], delta=delta)
        self.assertAlmostEqual(40.6930727, result.raw['center'][1], delta=delta)
        self.assertEqual("relation175905", result.raw['properties']['osm_id'])

    def test_geocode_exactly_one_false(self):
        list_result = self.geocode_run({"query": "New York", "exactly_one": False}, {})
        self.assertTrue(isinstance(list_result, list))

    def test_geocode_exactly_one_true(self):
        list_result = self.geocode_run({"query": "New York", "exactly_one": True}, {})
        self.assertTrue(isinstance(list_result, Location))
