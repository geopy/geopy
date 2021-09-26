import uuid

import pytest

from geopy import Point
from geopy.exc import GeocoderAuthenticationFailure, GeocoderQueryError
from geopy.geocoders import GeoNames
from test.geocoders.util import BaseTestGeocoder, env

try:
    import pytz
    pytz_available = True
except ImportError:
    pytz_available = False


class TestUnitGeoNames:

    def test_user_agent_custom(self):
        geocoder = GeoNames(
            username='DUMMYUSER_NORBERT',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'


class TestGeoNames(BaseTestGeocoder):

    delta = 0.04

    @classmethod
    def make_geocoder(cls, **kwargs):
        return GeoNames(username=env['GEONAMES_USERNAME'], **kwargs)

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "Mount Everest, Nepal"},
            {"latitude": 27.987, "longitude": 86.925},
        )

    async def test_query_urlencoding(self):
        location = await self.geocode_run(
            {"query": "Ry\u016b\u014d"},
            {"latitude": 35.65, "longitude": 138.5},
        )
        assert "Ry\u016b\u014d" in location.address

    async def test_reverse(self):
        location = await self.reverse_run(
            {
                "query": "40.75376406311989, -73.98489005863667",
            },
            {
                "latitude": 40.75376406311989,
                "longitude": -73.98489005863667,
            },
        )
        assert "Times Square" in location.address

    async def test_geocode_empty_response(self):
        await self.geocode_run(
            {"query": "sdlahaslkhdkasldhkjsahdlkash"},
            {},
            expect_failure=True,
        )

    async def test_reverse_nearby_place_name_raises_for_feature_code(self):
        with pytest.raises(ValueError):
            await self.reverse_run(
                {
                    "query": "40.75376406311989, -73.98489005863667",
                    "feature_code": "ADM1",
                },
                {},
            )

        with pytest.raises(ValueError):
            await self.reverse_run(
                {
                    "query": "40.75376406311989, -73.98489005863667",
                    "feature_code": "ADM1",
                    "find_nearby_type": "findNearbyPlaceName",
                },
                {},
            )

    async def test_reverse_nearby_place_name_lang(self):
        location = await self.reverse_run(
            {
                "query": "52.50, 13.41",
                "lang": 'ru',
            },
            {},
        )
        assert 'Берлин, Германия' in location.address

    async def test_reverse_find_nearby_raises_for_lang(self):
        with pytest.raises(ValueError):
            await self.reverse_run(
                {
                    "query": "40.75376406311989, -73.98489005863667",
                    "find_nearby_type": 'findNearby',
                    "lang": 'en',
                },
                {},
            )

    async def test_reverse_find_nearby(self):
        location = await self.reverse_run(
            {
                "query": "40.75376406311989, -73.98489005863667",
                "find_nearby_type": 'findNearby',
            },
            {
                "latitude": 40.75376406311989,
                "longitude": -73.98489005863667,
            },
        )
        assert "New York, United States" in location.address

    async def test_reverse_find_nearby_feature_code(self):
        await self.reverse_run(
            {
                "query": "40.75376406311989, -73.98489005863667",
                "find_nearby_type": 'findNearby',
                "feature_code": "ADM1",
            },
            {
                "latitude": 40.16706,
                "longitude": -74.49987,
            },
        )

    async def test_reverse_raises_for_unknown_find_nearby_type(self):
        with pytest.raises(GeocoderQueryError):
            await self.reverse_run(
                {
                    "query": "40.75376406311989, -73.98489005863667",
                    "find_nearby_type": "findSomethingNonExisting",
                },
                {},
            )

    @pytest.mark.skipif("not pytz_available")
    async def test_reverse_timezone(self):
        new_york_point = Point(40.75376406311989, -73.98489005863667)
        america_new_york = pytz.timezone("America/New_York")

        timezone = await self.reverse_timezone_run(
            {"query": new_york_point},
            america_new_york,
        )
        assert timezone.raw['countryCode'] == 'US'

    @pytest.mark.skipif("not pytz_available")
    async def test_reverse_timezone_unknown(self):
        await self.reverse_timezone_run(
            # Geonames doesn't return `timezoneId` for Antarctica,
            # but it provides GMT offset which can be used
            # to create a FixedOffset pytz timezone.
            {"query": "89.0, 1.0"},
            pytz.UTC,
        )
        await self.reverse_timezone_run(
            {"query": "89.0, 80.0"},
            pytz.FixedOffset(5 * 60),
        )

    async def test_country_str(self):
        await self.geocode_run(
            {"query": "kazan", "country": "TR"},
            {"latitude": 40.2317, "longitude": 32.6839},
        )

    async def test_country_list(self):
        await self.geocode_run(
            {"query": "kazan", "country": ["CN", "TR", "JP"]},
            {"latitude": 40.2317, "longitude": 32.6839},
        )

    async def test_country_bias(self):
        await self.geocode_run(
            {"query": "kazan", "country_bias": "TR"},
            {"latitude": 40.2317, "longitude": 32.6839},
        )


class TestGeoNamesInvalidAccount(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return GeoNames(
            username="geopy-not-existing-%s" % uuid.uuid4(),
            **kwargs
        )

    async def test_geocode(self):
        with pytest.raises(GeocoderAuthenticationFailure):
            await self.geocode_run(
                {"query": "moscow"},
                {},
                expect_failure=True,
            )

    @pytest.mark.skipif("not pytz_available")
    async def test_reverse_timezone(self):
        with pytest.raises(GeocoderAuthenticationFailure):
            await self.reverse_timezone_run(
                {"query": "40.6997716, -73.9753359"},
                None,
            )
