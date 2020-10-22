import pytest

from geopy.geocoders import MapTiler
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


@pytest.mark.skipif(
    not bool(env.get('MAPTILER_KEY')),
    reason="No MAPTILER_KEY env variable set"
)
class TestMapTiler(BaseTestGeocoder):
    @classmethod
    def make_geocoder(cls, **kwargs):
        return MapTiler(api_key=env['MAPTILER_KEY'], timeout=3, **kwargs)

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    async def test_unicode_name(self):
        await self.geocode_run(
            {"query": "Stadelhoferstrasse 8, 8001 Z\u00fcrich"},
            {"latitude": 47.36649, "longitude": 8.54855},
        )

    async def test_reverse(self):
        new_york_point = Point(40.75376406311989, -73.98489005863667)
        location = await self.reverse_run(
            {"query": new_york_point},
            {"latitude": 40.7537640, "longitude": -73.98489, "delta": 1},
        )
        assert "New York" in location.address

    async def test_zero_results(self):
        await self.geocode_run(
            {"query": 'asdfasdfasdf'},
            {},
            expect_failure=True,
        )

    async def test_geocode_outside_bbox(self):
        await self.geocode_run(
            {
                "query": "435 north michigan ave, chicago il 60611 usa",
                "bbox": [[34.172684, -118.604794],
                         [34.236144, -118.500938]]
            },
            {},
            expect_failure=True,
        )

    async def test_geocode_bbox(self):
        await self.geocode_run(
            {
                "query": "435 north michigan ave, chicago il 60611 usa",
                "bbox": [Point(35.227672, -103.271484),
                         Point(48.603858, -74.399414)]
            },
            {"latitude": 41.890, "longitude": -87.624},
        )

    async def test_geocode_proximity(self):
        await self.geocode_run(
            {"query": "200 queen street", "proximity": Point(45.3, -66.1)},
            {"latitude": 44.038901, "longitude": -64.73052, "delta": 0.1},
        )

    async def test_reverse_language(self):
        zurich_point = Point(47.3723, 8.5422)
        location = await self.reverse_run(
            {"query": zurich_point, "language": "ja"},
            {"latitude": 47.3723, "longitude": 8.5422, "delta": 1},
        )
        assert "\u30c1\u30e5\u30fc\u30ea\u30c3\u30d2" in location.address

    async def test_geocode_language(self):
        location = await self.geocode_run(
            {"query": "Z\u00fcrich", "language": "ja",
             "proximity": Point(47.3723, 8.5422)},
            {"latitude": 47.3723, "longitude": 8.5422, "delta": 1},
        )
        assert "\u30c1\u30e5\u30fc\u30ea\u30c3\u30d2" in location.address

    async def test_geocode_raw(self):
        result = await self.geocode_run({"query": "New York"}, {})
        delta = 1.0
        expected = pytest.approx((-73.8784155, 40.6930727), abs=delta)
        assert expected == result.raw['center']
        assert "relation175905" == result.raw['properties']['osm_id']

    async def test_geocode_exactly_one_false(self):
        list_result = await self.geocode_run(
            {"query": "maple street", "exactly_one": False},
            {},
        )
        assert len(list_result) >= 3
