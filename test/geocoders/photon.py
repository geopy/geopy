from geopy.geocoders import Photon
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder


class TestPhoton(BaseTestGeocoder):
    known_country_de = "Frankreich"
    known_country_fr = "France"

    @classmethod
    def make_geocoder(cls, **kwargs):
        return Photon(**kwargs)

    async def test_user_agent_custom(self):
        geocoder = Photon(
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    async def test_geocode(self):
        location = await self.geocode_run(
            {"query": "14 rue pelisson villeurbanne"},
            {"latitude": 45.7733963, "longitude": 4.88612369},
        )
        assert "France" in location.address

    async def test_osm_tag(self):
        await self.geocode_run(
            {"query": "Freedom", "osm_tag": "tourism:artwork"},
            {"latitude": 38.8898061, "longitude": -77.009088, "delta": 2.0},
        )

        await self.geocode_run(
            {"query": "Freedom", "osm_tag": ["!office", "place:hamlet"]},
            {"latitude": 44.3862491, "longitude": -88.290994, "delta": 2.0},
        )

    async def test_bbox(self):
        await self.geocode_run(
            {"query": "moscow", "language": "en"},
            {"latitude": 55.7504461, "longitude": 37.6174943},
        )
        await self.geocode_run(
            {"query": "moscow",  # Idaho USA
             "language": "en",
             "bbox": [[50.1, -130.1], [44.1, -100.9]]},
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )

    async def test_reverse(self):
        result = await self.reverse_run(
            {"query": Point(45.7733105, 4.8869339)},
            {"latitude": 45.7733105, "longitude": 4.8869339}
        )
        assert "France" in result.address

    async def test_geocode_language_parameter(self):
        result_geocode = await self.geocode_run(
            {"query": self.known_country_fr, "language": "de"},
            {},
        )
        assert (
            result_geocode.raw['properties']['country'] ==
            self.known_country_de
        )

    async def test_reverse_language_parameter(self):

        result_reverse_it = await self.reverse_run(
            {"query": "45.7733105, 4.8869339",
             "language": "de"},
            {},
        )
        assert (
            result_reverse_it.raw['properties']['country'] ==
            self.known_country_de
        )

        result_reverse_fr = await self.reverse_run(
            {"query": "45.7733105, 4.8869339",
             "language": "fr"},
            {},
        )
        assert (
            result_reverse_fr.raw['properties']['country'] ==
            self.known_country_fr
        )
