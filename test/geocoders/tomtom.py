from geopy.geocoders import TomTom
from test.geocoders.util import BaseTestGeocoder, env


class BaseTestTomTom(BaseTestGeocoder):

    async def test_user_agent_custom(self):
        geocoder = self.make_geocoder(
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    async def test_geocode(self):
        location = await self.geocode_run(
            {'query': 'moscow'},
            {'latitude': 55.75587, 'longitude': 37.61768},
        )
        assert 'Moscow' in location.address

    async def test_reverse(self):
        location = await self.reverse_run(
            {'query': '51.5285057, -0.1369635', 'language': 'en-US'},
            {'latitude': 51.5285057, 'longitude': -0.1369635,
             "delta": 0.3},
        )
        assert 'London' in location.address
        # Russian Moscow address can be reported differently, so
        # we're querying something more ordinary, like London.
        #
        # For example, AzureMaps might return
        # `Красная площадь, 109012 Moskva` instead of the expected
        # `Красная площадь, 109012 Москва`, even when language is
        # specified explicitly as `ru-RU`. And TomTom always returns
        # the cyrillic variant, even when the `en-US` language is
        # requested.

    async def test_geocode_empty(self):
        await self.geocode_run(
            {'query': 'sldkfhdskjfhsdkhgflaskjgf'},
            {},
            expect_failure=True,
        )


class TestTomTom(BaseTestTomTom):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return TomTom(env['TOMTOM_KEY'], timeout=3,
                      **kwargs)
