import pytest

from geopy.exc import GeocoderQueryError
from geopy.geocoders import USCensus
from test.geocoders.util import BaseTestGeocoder


class TestUSCensus(BaseTestGeocoder):

    query = '435 north michigan ave, chicago il 60611 usa'
    structured_query = {
        'street': '435 north michigan ave',
        'city': 'chicago',
        'stage': 'il',
        'zip': '60611'
    }
    expected_coordinate = {'latitude': 41.890, 'longitude': -87.624}

    @classmethod
    def make_geocoder(cls, **kwargs):
        return USCensus(**kwargs)

    async def test_geocode_query(self):
        await self.geocode_run(
            {'query': self.query},
            self.expected_coordinate,
        )

    async def test_geocode_structured_query(self):
        await self.geocode_run(
            {'query': self.structured_query},
            self.expected_coordinate,
        )

    async def test_geocode_invalid_query(self):
        with pytest.raises(GeocoderQueryError):
            await self.geocode_run(
                {'query': ''},
                {},
                expect_failure=True
            )

    async def test_geocode_empty_result(self):
        result = await self.geocode_run(
            {'query': 'dsadjkasdjasd'},
            {},
            expect_failure=True,
        )
        assert(result is None)

    async def test_no_geolookup_by_default(self):
        result = await self.geocode_run(
            {'query': self.query},
            self.expected_coordinate,
        )
        assert('geographies' not in result.raw)

    async def test_no_geolookup_ignores_geolookup_params(self):
        result = await self.geocode_run(
            {
                'query': self.query,
                'geolookup': False,
                'geography_vintage': 'Current',
                'layers': 'Counties'
            },
            self.expected_coordinate,
        )
        assert('geographies' not in result.raw)

    async def test_default_geolookup(self):
        result = await self.geocode_run(
            {
                'query': self.query,
                'geolookup': True
            },
            self.expected_coordinate
        )
        assert ('geographies' in result.raw)

    async def test_geolookup_layers_as_string(self):
        result = await self.geocode_run(
            {
                'query': self.query,
                'geolookup': True,
                'geography_vintage': 'Current',
                'layers': 'Unified School Districts,Secondary School Districts'
            },
            self.expected_coordinate,
        )
        assert('geographies' in result.raw)
        assert(len(result.raw['geographies']) == 2)
        assert('Unified School Districts' in result.raw['geographies'])
        assert('Secondary School Districts' in result.raw['geographies'])

    async def test_geolookup_layers_as_sequence(self):
        result = await self.geocode_run(
            {
                'query': self.query,
                'geolookup': True,
                'geography_vintage': 'Current',
                'layers': ['Counties', 'States']
            },
            self.expected_coordinate,
        )
        assert('geographies' in result.raw)
        assert('Counties' in result.raw['geographies'])
        assert('States' in result.raw['geographies'])

    async def test_geolookup_empty_layers(self):
        result = await self.geocode_run(
            {
                'query': self.query,
                'geolookup': True,
                'geography_vintage': 'Current',
                'layers': []
            },
            self.expected_coordinate,
        )
        assert('geographies' in result.raw)

    async def test_geolookup_invalid_layer(self):
        result = await self.geocode_run(
            {
                'query': self.query,
                'geolookup': True,
                'geography_vintage': 'Current',
                'layers': ['-1']
            },
            self.expected_coordinate,
        )
        assert('geographies' in result.raw)

    async def test_geolookup_invalid_geography_vintage(self):
        with pytest.raises(GeocoderQueryError):
            await self.geocode_run(
                {
                    'query': self.query,
                    'geolookup': True,
                    'geography_vintage': '',
                },
                self.expected_coordinate,
            )
