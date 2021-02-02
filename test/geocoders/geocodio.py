import pytest

from geopy import exc
from geopy.geocoders import Geocodio
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


class TestGeocodio(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        api_key = kwargs.pop('api_key') if 'api_key' in kwargs else env['GEOCODIO_KEY']
        return Geocodio(api_key=api_key, **kwargs)

    async def test_user_agent_custom(self):
        geocoder = self.make_geocoder(user_agent='my_user_agent/1.0')
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    async def test_error_with_no_api_key(self):
        with pytest.raises(exc.ConfigurationError):
            self.make_geocoder(api_key=None)

    async def test_error_with_query_and_street(self):
        with pytest.raises(exc.GeocoderQueryError):
            await self.geocode_run(
                {
                    'query': '435 north michigan ave, chicago il 60611 usa',
                    'street': '435 north michigan ave'
                },
                {},
                expect_failure=True
            )

    async def test_error_with_only_street(self):
        with pytest.raises(exc.GeocoderQueryError):
            await self.geocode_run(
                {
                    'street': '435 north michigan ave'
                },
                {},
                expect_failure=True
            )

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.89037, "longitude": -87.623192},
        )

    async def test_geocode_from_components(self):
        await self.geocode_run(
            {
                "street": "435 north michigan ave",
                "city": "chicago",
                "state": "IL",
                "postal_code": "60611"
            },
            {"latitude": 41.89037, "longitude": -87.623192},
        )

    async def test_zero_results(self):
        with pytest.raises(exc.GeocoderQueryError) as excinfo:
            await self.geocode_run(
                {"query": ''},
                {},
                expect_failure=True,
            )

        assert str(excinfo.value) == 'Could not geocode address. ' \
                                     'Postal code or city required.'

    async def test_reverse(self):
        location = await self.reverse_run(
            {"query": Point(40.75376406311989, -73.98489005863667)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
            skiptest_on_failure=True,  # sometimes the result is empty
        )
        assert "new york" in location.address.lower()
