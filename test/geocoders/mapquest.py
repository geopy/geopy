import unittest

from geopy.compat import u
from geopy.geocoders import MapQuest
from geopy.point import Point
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(
    bool(env.get('MAPQUEST_KEY')),
    "No MAPQUEST_KEY env variable set"
)
class MapQuestTestCase(GeocoderTestBase):
    @classmethod
    def setUpClass(cls):
        cls.geocoder = MapQuest(api_key=env['MAPQUEST_KEY'], timeout=3)

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
            {"query": new_york_point},
            {"latitude": 40.7537640, "longitude": -73.98489, "delta": 1},
        )
        assert "New York" in location.address

    def test_zero_results(self):
        self.geocode_run(
            {"query": ''},
            {},
            expect_failure=True,
        )

    def test_geocode_empty(self):
        self.geocode_run(
            {'query': 'sldkfhdskjfhsdkhgflaskjgf'},
            {},
            expect_failure=True,
        )

    def test_geocode_bbox(self):
        self.geocode_run(
            {
                "query": "435 north michigan ave, chicago il 60611 usa",
                "bounds": [Point(35.227672, -103.271484),
                           Point(48.603858, -74.399414)]
            },
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_geocode_raw(self):
        result = self.geocode_run(
            {"query": "New York"},
            {"latitude": 40.713054, "longitude": -74.007228, "delta": 1},
        )
        assert result.raw['adminArea1'] == "US"

    def test_geocode_limit(self):
        list_result = self.geocode_run(
            {"query": "maple street", "exactly_one": False, "limit": 2},
            {},
        )
        assert len(list_result) == 2

        list_result = self.geocode_run(
            {"query": "maple street", "exactly_one": False, "limit": 4},
            {},
        )
        assert len(list_result) == 4
