from geopy.geocoders import GeocodeAPI
from test.geocoders.util import BaseTestGeocoder, env


class TestGeocodeAPI(BaseTestGeocoder):
    @classmethod
    def make_geocoder(cls, **kwargs):
        # return GeocodeAPI(env.get('GEOCODEAPI_KEY'), **kwargs)
        return GeocodeAPI('8e502d80-1f4e-11eb-8913-e723b130bf53', **kwargs)

    async def test_geocode(self):
        location = await self.geocode_run(
            {'query': '435 north michigan ave, chicago il 60611 usa'},
            {'latitude': 41.89037, 'longitude': -87.623192},
        )
        assert 'chicago' in location.address.lower()
