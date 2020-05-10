import unittest

from geopy.geocoders import AlgoliaPlaces
from test.geocoders.tomtom import BaseTomTomTestCase
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(
    bool(env.get('ALGOLIA_PLACES_APP_ID')) and bool(env.get('ALGOLIA_PLACES_API_KEY')),
    'No ALGOLIA_PLACES_APP_ID and/or no ALGOLIA_PLACES_API_KEY env variables setted'
)
class AlgoliaPlacesTestCase(BaseTomTomTestCase, GeocoderTestBase):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return AlgoliaPlaces(
            env['ALGOLIA_PLACES_APP_ID'],
            env['ALGOLIA_PLACES_API_KEY'],
            timeout=3,
            **kwargs)

    def test_reverse(self):
        location = self.reverse_run(
            {'query': '51, -0.13', 'language': 'en'},
            {'latitude': 51, 'longitude': -0.13},
        )
        self.assertIn('A272', location.address)

    def test_reverse_no_result(self):
        self.reverse_run(
            # North Atlantic Ocean
            {'query': (35.173809, -37.485351)},
            {},
            expect_failure=True
        )

    def test_explicit_type(self):
        location = self.geocode_run(
            {'query': 'Madrid', 'type': 'city', 'language': 'en'},
            {},
        )
        self.assertIn('Madrid', location.address)

    def test_limit(self):
        limit = 5
        locations = self.geocode_run(
            {'query': 'Madrid', 'type': 'city',
             'language': 'en', 'exactly_one': False,
             'limit': limit},
            {},
        )
        self.assertEqual(len(locations), limit)

    def test_countries(self):
        countries = ["ES"]
        locations = self.geocode_run(
            {'query': 'Madrid', 'language': 'en',
             'exactly_one': False, 'countries': countries},
            {},
        )

    def test_countries_no_result(self):
        countries = ["NO", "IT"]
        locations = self.geocode_run(
            {'query': 'Madrid', 'language': 'en',
             'exactly_one': False, 'countries': countries},
            {},
            expect_failure=True
        )

    def test_geocode_no_result(self):
        self.geocode_run(
            {'query': 'sldkfhdskjfhsdkhgflaskjgf'},
            {},
            expect_failure=True,
        )
