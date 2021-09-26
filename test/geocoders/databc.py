import pytest

from geopy.exc import GeocoderQueryError
from geopy.geocoders import DataBC
from test.geocoders.util import BaseTestGeocoder


class TestDataBC(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return DataBC(**kwargs)

    async def test_user_agent_custom(self):
        geocoder = DataBC(
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "135 North Pym Road, Parksville"},
            {"latitude": 49.321, "longitude": -124.337},
        )

    async def test_multiple_results(self):
        res = await self.geocode_run(
            {"query": "1st St", "exactly_one": False},
            {},
        )
        assert len(res) > 1

    async def test_optional_params(self):
        await self.geocode_run(
            {"query": "5670 malibu terrace nanaimo bc",
             "location_descriptor": "accessPoint",
             "set_back": 100},
            {"latitude": 49.2299, "longitude": -124.0163},
        )

    async def test_query_error(self):
        with pytest.raises(GeocoderQueryError):
            await self.geocode_run(
                {"query": "1 Main St, Vancouver",
                 "location_descriptor": "access_Point"},
                {},
                expect_failure=True,
            )
