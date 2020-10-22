from geopy.geocoders import AlgoliaPlaces
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


class TestAlgoliaPlaces(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return AlgoliaPlaces(
            app_id=env.get('ALGOLIA_PLACES_APP_ID'),
            api_key=env.get('ALGOLIA_PLACES_API_KEY'),
            timeout=3,
            **kwargs)

    async def test_user_agent_custom(self):
        geocoder = self.make_geocoder(
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    async def test_geocode(self):
        location = await self.geocode_run(
            {'query': 'москва'},
            {'latitude': 55.75587, 'longitude': 37.61768},
        )
        assert 'Москва' in location.address

    async def test_reverse(self):
        location = await self.reverse_run(
            {'query': '51, -0.13', 'language': 'en'},
            {'latitude': 51, 'longitude': -0.13},
        )
        assert 'A272' in location.address

    async def test_reverse_no_result(self):
        await self.reverse_run(
            # North Atlantic Ocean
            {'query': (35.173809, -37.485351)},
            {},
            expect_failure=True
        )

    async def test_explicit_type(self):
        location = await self.geocode_run(
            {'query': 'Madrid', 'type': 'city', 'language': 'en'},
            {},
        )
        assert 'Madrid' in location.address

    async def test_limit(self):
        limit = 5
        locations = await self.geocode_run(
            {'query': 'Madrid', 'type': 'city',
             'language': 'en', 'exactly_one': False,
             'limit': limit},
            {},
        )
        assert len(locations) == limit

    async def test_countries(self):
        countries = ["ES"]
        location = await self.geocode_run(
            {'query': 'Madrid', 'language': 'en',
             'countries': countries},
            {},
        )
        assert "Madrid" in location.address

    async def test_countries_no_result(self):
        countries = ["NO", "IT"]
        await self.geocode_run(
            {'query': 'Madrid', 'language': 'en',
             'countries': countries},
            {},
            expect_failure=True
        )

    async def test_geocode_no_result(self):
        await self.geocode_run(
            {'query': 'sldkfhdskjfhsdkhgflaskjgf'},
            {},
            expect_failure=True,
        )

    async def test_around(self):
        await self.geocode_run(
            {'query': 'maple street', 'language': 'en', 'around': Point(51.1, -0.1)},
            {'latitude': 51.5299, 'longitude': -0.0628044, "delta": 1},
        )
        await self.geocode_run(
            {'query': 'maple street', 'language': 'en', 'around': Point(50.1, 10.1)},
            {'latitude': 50.0517, 'longitude': 10.1966, "delta": 1},
        )
