from geopy.geocoders import MapQuest
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


class TestMapQuest(BaseTestGeocoder):
    @classmethod
    def make_geocoder(cls, **kwargs):
        return MapQuest(api_key=env['MAPQUEST_KEY'], timeout=3, **kwargs)

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.89036, "longitude": -87.624043},
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
            {"query": ''},
            {},
            expect_failure=True,
        )

    async def test_geocode_bbox(self):
        await self.geocode_run(
            {
                "query": "435 north michigan ave, chicago il 60611 usa",
                "bounds": [Point(35.227672, -103.271484),
                           Point(48.603858, -74.399414)]
            },
            {"latitude": 41.890, "longitude": -87.624},
        )

    async def test_geocode_raw(self):
        result = await self.geocode_run(
            {"query": "New York"},
            {"latitude": 40.713054, "longitude": -74.007228, "delta": 1},
        )
        assert result.raw['adminArea1'] == "US"

    async def test_geocode_limit(self):
        list_result = await self.geocode_run(
            {"query": "maple street", "exactly_one": False, "limit": 2},
            {},
        )
        assert len(list_result) == 2

        list_result = await self.geocode_run(
            {"query": "maple street", "exactly_one": False, "limit": 4},
            {},
        )
        assert len(list_result) == 4
