import warnings

from geopy.geocoders import Pelias
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


class BaseTestPelias(BaseTestGeocoder):

    delta = 0.04
    known_state_de = "Verwaltungsregion Ionische Inseln"
    known_state_en = "Ionian Islands Periphery"

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )
        await self.geocode_run(
            {"query": "san josé california"},
            {"latitude": 37.33939, "longitude": -121.89496},
        )

    async def test_reverse(self):
        await self.reverse_run(
            {"query": Point(40.75376406311989, -73.98489005863667)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667}
        )

    async def test_boundary_rect(self):
        await self.geocode_run(
            {"query": "moscow",  # Idaho USA
             "boundary_rect": [[50.1, -130.1], [44.1, -100.9]]},
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )

    async def test_geocode_language_parameter(self):
        query = "Graben 7, Wien"
        result_geocode = await self.geocode_run(
            {"query": query, "language": "de"}, {}
        )
        assert result_geocode.raw['properties']['country'] == "Österreich"

        result_geocode = await self.geocode_run(
            {"query": query, "language": "en"}, {}
        )
        assert result_geocode.raw['properties']['country'] == "Austria"

    async def test_reverse_language_parameter(self):
        query = "48.198674, 16.348388"
        result_reverse_de = await self.reverse_run(
            {"query": query, "language": "de"},
            {},
        )
        assert result_reverse_de.raw['properties']['country'] == "Österreich"

        result_reverse_en = await self.reverse_run(
            {"query": query, "language": "en"},
            {},
        )
        assert result_reverse_en.raw['properties']['country'] == "Austria"

    async def test_geocode_country_bias(self):
        await self.geocode_run(
            {"query": "moscow"},
            {"latitude": 55.7504461, "longitude": 37.6174943},
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            await self.geocode_run(
                {"query": "moscow",  # Idaho USA
                 "country_bias": "USA"},
                {"latitude": 46.7323875, "longitude": -117.0001651},
            )
            assert len(w) == 1

    async def test_geocode_countries(self):
        await self.geocode_run(
            {"query": "moscow"},
            {"latitude": 55.7504461, "longitude": 37.6174943},
        )
        await self.geocode_run(
            {"query": "moscow",  # Idaho USA
             "countries": ["USA", "CAN"]},
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )


class TestPelias(BaseTestPelias):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return Pelias(
            env['PELIAS_DOMAIN'],
            api_key=env['PELIAS_KEY'],
            **kwargs,
        )
