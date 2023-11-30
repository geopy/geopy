import pytest

from geopy import exc
from geopy.geocoders import GeocodeAPI
from geopy.point import Point

from test.geocoders.util import BaseTestGeocoder, env


class TestGeocodeAPI(BaseTestGeocoder):
    @classmethod
    def make_geocoder(cls, **kwargs):
        return GeocodeAPI(env["GEOCODEAPI_KEY"], **kwargs)

    async def test_geocode(self):
        location = await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.89037, "longitude": -87.623192},
        )
        assert "chicago" in location.address.lower()

    async def test_location_address(self):
        await self.geocode_run(
            {"query": "moscow"},
            {
                "address": "Moscow, Russia",
                "latitude": 55.7558913503453,
                "longitude": 37.6172961632184,
            },
        )

    async def test_reverse(self):
        location = await self.reverse_run(
            {"query": Point(40.75376406311989, -73.98489005863667)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )
        assert "new york" in location.address.lower()

    async def test_authentication_failure(self):
        async with self.inject_geocoder(GeocodeAPI(api_key="invalid")):
            with pytest.raises(exc.GeocoderInsufficientPrivileges):
                await self.geocode_run(
                    {"query": "435 north michigan ave, chicago il 60611"},
                    {},
                    expect_failure=True,
                )

    async def test_no_results(self):
        await self.geocode_run(
            {"query": "gibberish kdjhsakdjh skjdhsakjdh"}, {}, expect_failure=True
        )
