import unittest

import pytest

from geopy.compat import u
from geopy.geocoders import MapBox
from geopy.point import Point
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(
    bool(env.get('MAPBOX_KEY')),
    "No MAPBOX_KEY env variable set"
)
class MapBoxTestCase(GeocoderTestBase):
    @classmethod
    def setUpClass(cls):
        cls.geocoder = MapBox(api_key=env['MAPBOX_KEY'], timeout=3)

    def test_geocode(self):
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        self.geocode_run(
            {"query": u("\u6545\u5bab")},
            {"latitude": 39.916, "longitude": 116.390},
        )

    def test_reverse(self):
        new_york_point = Point(40.75376406311989, -73.98489005863667)
        location = self.reverse_run(
            {"query": new_york_point},
            {"latitude": 40.7537640, "longitude": -73.98489, "delta": 1},
        )
        assert "New York" in location.address

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
            {"latitude": 45.270208, "longitude": -66.050289, "delta": 0.1},
        )

    def test_geocode_country_str(self):
        self.geocode_run(
            {"query": "kazan", "country": "TR"},
            {"latitude": 40.2317, "longitude": 32.6839},
        )

    def test_geocode_country_list(self):
        self.geocode_run(
            {"query": "kazan", "country": ["CN", "TR"]},
            {"latitude": 40.2317, "longitude": 32.6839},
        )

    def test_geocode_raw(self):
        result = self.geocode_run({"query": "New York"}, {})
        delta = 1.0
        expected = pytest.approx((-73.8784155, 40.6930727), abs=delta)
        assert expected == result.raw['center']

    def test_geocode_exactly_one_false(self):
        list_result = self.geocode_run(
            {"query": "maple street", "exactly_one": False},
            {},
        )
        assert len(list_result) >= 3
