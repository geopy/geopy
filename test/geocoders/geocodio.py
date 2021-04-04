import pytest

from geopy import exc
from geopy.geocoders import Geocodio
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


class TestGeocodio(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return Geocodio(api_key=env['GEOCODIO_KEY'], **kwargs)

    async def test_user_agent_custom(self):
        geocoder = self.make_geocoder(user_agent='my_user_agent/1.0')
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    async def test_error_with_only_street(self):
        with pytest.raises(exc.GeocoderQueryError):
            await self.geocode_run(
                {'query': {'street': '435 north michigan ave'}},
                {},
            )

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.89037, "longitude": -87.623192},
        )

    async def test_geocode_from_components(self):
        await self.geocode_run(
            {
                "query": {
                    "street": "435 north michigan ave",
                    "city": "chicago",
                    "state": "IL",
                    "postal_code": "60611"
                },
            },
            {"latitude": 41.89037, "longitude": -87.623192},
        )

    async def test_geocode_many_results(self):
        result = await self.geocode_run(
            {"query": "Springfield", "exactly_one": False},
            {}
        )
        assert len(result) > 1

    async def test_reverse(self):
        location = await self.reverse_run(
            {"query": Point(40.75376406311989, -73.98489005863667)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )
        assert "new york" in location.address.lower()

    async def test_geocode_no_result(self):
        await self.geocode_run(
            {"query": "dksajdkjashdkjashdjasghd"},
            {},
            expect_failure=True,
        )

    async def test_geocode_structured_no_result(self):
        await self.geocode_run(
            {"query": {"city": "dkasdjksahdksajhd", "street": "sdahaskjdhask"}},
            {},
            expect_failure=True,
        )

    async def test_reverse_no_result(self):
        await self.reverse_run(
            # North Atlantic Ocean
            {"query": (35.173809, -37.485351)},
            {},
            expect_failure=True,
        )
