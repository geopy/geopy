import pytest

from geopy import exc
from geopy.geocoders import ArcGIS
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


class TestUnitArcGIS:

    def test_user_agent_custom(self):
        geocoder = ArcGIS(
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'


class TestArcGIS(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return ArcGIS(timeout=3, **kwargs)

    async def test_missing_password_error(self):
        with pytest.raises(exc.ConfigurationError):
            ArcGIS(username='a')

    async def test_scheme_config_error(self):
        with pytest.raises(exc.ConfigurationError):
            ArcGIS(
                username='a',
                password='b',
                referer='http://www.example.com',
                scheme='http'
            )

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    async def test_empty_response(self):
        await self.geocode_run(
            {"query": "dksahdksahdjksahdoufydshf"},
            {},
            expect_failure=True
        )

    async def test_geocode_with_out_fields_string(self):
        result = await self.geocode_run(
            {"query": "Trafalgar Square, London",
             "out_fields": "Country"},
            {}
        )
        assert result.raw['attributes'] == {'Country': 'GBR'}

    async def test_geocode_with_out_fields_list(self):
        result = await self.geocode_run(
            {"query": "Trafalgar Square, London",
             "out_fields": ["City", "Type"]},
            {}
        )
        assert result.raw['attributes'] == {
            'City': 'London', 'Type': 'Tourist Attraction'
        }

    async def test_reverse_point(self):
        location = await self.reverse_run(
            {"query": Point(40.753898, -73.985071)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )
        assert 'New York' in location.address

    async def test_reverse_not_exactly_one(self):
        await self.reverse_run(
            {"query": Point(40.753898, -73.985071), "exactly_one": False},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    async def test_reverse_long_label_address(self):
        await self.reverse_run(
            {"query": (35.173809, -37.485351)},
            {"address": "Atlantic Ocean"},
        )


class TestArcGISAuthenticated(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return ArcGIS(
            username=env['ARCGIS_USERNAME'],
            password=env['ARCGIS_PASSWORD'],
            referer=env['ARCGIS_REFERER'],
            timeout=3,
            **kwargs
        )

    async def test_basic_address(self):
        await self.geocode_run(
            {"query": "Potsdamer Platz, Berlin, Deutschland"},
            {"latitude": 52.5094982, "longitude": 13.3765983, "delta": 4},
        )
