import pytest

from geopy import exc
from geopy.adapters import BaseSyncAdapter
from geopy.geocoders import OpenGeocoding
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


class RecordingAdapter(BaseSyncAdapter):
    response = None

    def __init__(self, *, proxies, ssl_context):
        super().__init__(proxies=proxies, ssl_context=ssl_context)
        self.requests = []

    def get_json(self, url, *, timeout, headers):
        self.requests.append((url, headers))
        return self.response

    def get_text(self, url, *, timeout, headers):  # pragma: no cover
        raise NotImplementedError


class TestUnitOpenGeocoding:

    def make_geocoder(self, response):
        RecordingAdapter.response = response
        return OpenGeocoding(api_key='og_test', adapter_factory=RecordingAdapter)

    def test_key_is_sent_in_header_not_url(self):
        geocoder = self.make_geocoder({})
        geocoder.geocode('Rådhuspladsen 1, København')
        url, headers = geocoder.adapter.requests[0]
        assert url == (
            'https://api.opengeocoding.com/v1/search?'
            'addressString=R%C3%A5dhuspladsen+1%2C+K%C3%B8benhavn'
        )
        assert headers['x-api-key'] == 'og_test'
        assert 'og_test' not in url

    def test_geocode_parses_single_result(self):
        raw = {
            'displayName': 'Example Street 1, Example City',
            'geoCoordinates': {'lat': 1.5, 'lon': 2.5},
            'goodMatch': True,
        }
        geocoder = self.make_geocoder(raw)
        location = geocoder.geocode('Example Street 1')
        assert (location.address, location.latitude, location.longitude) == (
            'Example Street 1, Example City', 1.5, 2.5)
        assert location.raw == raw
        assert [loc.raw for loc in geocoder.geocode('x', exactly_one=False)] == [raw]

    def test_geocode_empty_response_is_none(self):
        geocoder = self.make_geocoder({})
        assert geocoder.geocode('nothing') is None
        assert geocoder.geocode('nothing', exactly_one=False) is None

    def test_zero_coordinates_omitted_by_json_encoding(self):
        geocoder = self.make_geocoder(
            {'displayName': 'Null Island', 'geoCoordinates': {}})
        assert geocoder.geocode('x') is None
        geocoder = self.make_geocoder(
            {'displayName': 'Equator', 'geoCoordinates': {'lon': 9.0}})
        assert geocoder.geocode('x').point[:2] == (0.0, 9.0)

    def test_reverse_request_and_results(self):
        results = [
            {'address': {'displayName': name,
                         'geoCoordinates': {'lat': 1.0, 'lon': 2.0}},
             'distanceM': 3.0, 'layer': 'address'}
            for name in ('A', 'B')
        ]
        geocoder = self.make_geocoder({'results': results})
        locations = geocoder.reverse(
            Point(55.5, 12.5), exactly_one=False, radius=200, limit=2)
        url, _ = geocoder.adapter.requests[0]
        assert url == ('https://api.opengeocoding.com/v1/reverse?'
                       'lat=55.5&lon=12.5&radiusM=200&size=2')
        assert [loc.address for loc in locations] == ['A', 'B']
        assert locations[0].raw == results[0]

        assert geocoder.reverse('55.5, 12.5').address == 'A'
        url, _ = geocoder.adapter.requests[1]
        assert url.endswith('lat=55.5&lon=12.5&size=1')

    def test_reverse_empty_response_is_none(self):
        geocoder = self.make_geocoder({})
        assert geocoder.reverse(Point(0, 0)) is None


class TestOpenGeocoding(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return OpenGeocoding(api_key=env['OPENGEOCODING_KEY'], timeout=10, **kwargs)

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    async def test_geocode_exactly_one_false(self):
        result = await self.geocode_run(
            {"query": "Rådhuspladsen 1, 1550 København", "exactly_one": False},
            {"latitude": 55.676, "longitude": 12.569},
        )
        assert len(result) == 1

    async def test_geocode_empty_result(self):
        await self.geocode_run(
            {"query": "xqzjvw qxzjv"},
            {},
            expect_failure=True,
        )

    async def test_reverse(self):
        location = await self.reverse_run(
            {"query": Point(40.74843, -73.98566)},
            {"latitude": 40.74843, "longitude": -73.98566},
        )
        assert "New York" in location.address

    async def test_reverse_limit(self):
        result = await self.reverse_run(
            {"query": Point(40.74843, -73.98566), "exactly_one": False,
             "limit": 3},
            {"latitude": 40.74843, "longitude": -73.98566},
        )
        assert 1 <= len(result) <= 3

    async def test_invalid_key(self):
        async with self.inject_geocoder(OpenGeocoding(api_key='og_invalid')):
            with pytest.raises(exc.GeocoderAuthenticationFailure):
                await self.geocode_run(
                    {"query": "Copenhagen"}, {}, skiptest_on_errors=False)
