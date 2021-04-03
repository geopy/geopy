from geopy.geocoders import HereV7
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


class TestHereV7(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return HereV7(env['HERE_APIKEY'], **kwargs)

    async def test_geocode_empty_result(self):
        await self.geocode_run(
            {"query": "xqj37"},
            {},
            expect_failure=True
        )

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624}
        )

    async def test_geocode_query_and_components(self):
        query = "435 north michigan ave"
        components = {
            "city": "chicago",
            "state": "il",
            "postalCode": 60611,
            "country": "usa",
        }
        await self.geocode_run(
            {"query": query, "components": components},
            {"latitude": 41.890, "longitude": -87.624}
        )

    async def test_geocode_structured(self):
        components = {
            "street": "north michigan ave",
            "houseNumber": "435",
            "city": "chicago",
            "state": "il",
            "postalCode": 60611,
            "country": "usa",
        }
        await self.geocode_run(
            {"components": components},
            {"latitude": 41.890, "longitude": -87.624}
        )

    async def test_geocode_unicode_name(self):
        # unicode in Japanese for Paris. (POIs not included.)
        await self.geocode_run(
            {"query": "\u30d1\u30ea"},
            {"latitude": 48.85718, "longitude": 2.34141}
        )

    async def test_geocode_at(self):
        await self.geocode_run(
            {
                "query": "moscow",  # Idaho USA
                "at": (46.734303, -116.999558)
            },
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )

    async def test_geocode_countries(self):
        await self.geocode_run(
            {
                "query": "moscow",  # Idaho USA
                "countries": ["USA", "CAN"],
            },
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )

    async def test_geocode_language(self):
        address_string = "435 north michigan ave, chicago il 60611 usa"
        res = await self.geocode_run(
            {"query": address_string, "language": "de-DE"},
            {}
        )
        assert "Vereinigte Staaten" in res.address

        res = await self.geocode_run(
            {"query": address_string, "language": "en-US"},
            {}
        )
        assert "United States" in res.address

    async def test_geocode_limit(self):
        res = await self.geocode_run(
            {
                "query": "maple street",
                "limit": 5,
                "exactly_one": False
            },
            {}
        )
        assert len(res) == 5

    async def test_reverse(self):
        await self.reverse_run(
            {"query": Point(40.753898, -73.985071)},
            {"latitude": 40.753898, "longitude": -73.985071}
        )

    async def test_reverse_language(self):
        res = await self.reverse_run(
            {"query": Point(40.753898, -73.985071), "language": "de-DE"},
            {}
        )
        assert "Vereinigte Staaten" in res.address

        res = await self.reverse_run(
            {"query": Point(40.753898, -73.985071), "language": "en-US"},
            {}
        )
        assert "United States" in res.address

    async def test_reverse_limit(self):
        res = await self.reverse_run(
            {
                "query": Point(40.753898, -73.985071),
                "limit": 5,
                "exactly_one": False
            },
            {}
        )
        assert len(res) == 5
