from datetime import datetime

import pytest

from geopy.exc import GeocoderAuthenticationFailure, GeocoderQueryError
from geopy.geocoders import MyGeocode
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env

try:
    import pytz
    pytz_available = True
except ImportError:
    pytz_available = False


class TestUnitMyGeocode:

    def test_user_agent_custom(self):
        geocoder = MyGeocode(
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'


class TestMyGeocode(BaseTestGeocoder):

    delta = 0.01

    @classmethod
    def make_geocoder(cls, **kwargs):
        return MyGeocode(
            api_key=env.get('MYGEOCODE_KEY'),
            timeout=10,
            **kwargs
        )

    async def test_geocode(self):
        location = await self.geocode_run(
            {"query": "Dam 1, Amsterdam"},
            {"latitude": 52.373294, "longitude": 4.893716},
        )
        assert location.raw['components']['country_code'] == 'nl'

    async def test_geocode_structured(self):
        await self.geocode_run(
            {"query": {"street": "Dam 1", "city": "Amsterdam", "country": "nl"}},
            {"latitude": 52.373294, "longitude": 4.893716},
        )

    async def test_geocode_empty_result(self):
        await self.geocode_run(
            {"query": "dksajdkjashdkjashdjasghd"},
            {},
            expect_failure=True,
        )

    async def test_geocode_limit(self):
        result = await self.geocode_run(
            {"query": "Springfield", "exactly_one": False, "limit": 3},
            {},
        )
        assert 1 < len(result) <= 3

    async def test_geocode_countries(self):
        location = await self.geocode_run(
            {"query": "Paris", "countries": "us"},
            {},
        )
        assert location.raw['components']['country_code'] == 'us'

        location = await self.geocode_run(
            {"query": "Paris", "countries": ["ca", "us"]},
            {},
        )
        assert location.raw['components']['country_code'] in ('ca', 'us')

    async def test_geocode_language(self):
        location = await self.geocode_run(
            {"query": "Graben 7, Wien", "language": "de"},
            {},
        )
        assert location.raw['components']['country'] == "Österreich"

    async def test_geocode_bounded(self):
        result = await self.geocode_run(
            {"query": "Berlin", "bounds": [(24, -125), (50, -66)], "bounded": True,
             "exactly_one": False},
            {},
        )
        assert all(
            location.raw['components']['country_code'] == 'us' for location in result
        )

    async def test_geocode_types(self):
        result = await self.geocode_run(
            {"query": "Springfield", "types": "city", "exactly_one": False},
            {},
        )
        assert all(location.raw['type'] == 'city' for location in result)

    async def test_geocode_place_id(self):
        location = await self.geocode_run(
            {"query": "Dam 1, Amsterdam"},
            {"latitude": 52.373294, "longitude": 4.893716},
        )
        await self.geocode_run(
            {"place_id": location.raw['place_id']},
            {"latitude": 52.373294, "longitude": 4.893716},
        )

    async def test_geocode_place_id_with_query(self):
        with pytest.raises(ValueError):
            await self.geocode_run(
                {"query": "Dam 1, Amsterdam", "place_id": "abc"},
                {},
            )

    async def test_geocode_typeahead(self):
        location = await self.geocode_run(
            {"query": "Amsterd", "countries": "nl", "typeahead": True},
            {"latitude": 52.37, "longitude": 4.89, "delta": 0.1},
        )
        assert "Amsterdam" in location.address

    async def test_geocode_typeahead_structured(self):
        with pytest.raises(ValueError):
            await self.geocode_run(
                {"query": {"city": "Amsterdam"}, "typeahead": True},
                {},
            )

    async def test_geocode_annotations(self):
        location = await self.geocode_run(
            {"query": "Dam 1, Amsterdam", "annotations": True},
            {},
        )
        assert location.raw['timezone']['id'] == 'Europe/Amsterdam'

    async def test_reverse(self):
        location = await self.reverse_run(
            {"query": Point(41.8902, 12.4922)},
            {"latitude": 41.8902, "longitude": 12.4922},
        )
        assert "Roma" in location.address

    async def test_reverse_not_exactly_one(self):
        result = await self.reverse_run(
            {"query": "41.8902, 12.4922", "exactly_one": False},
            {"latitude": 41.8902, "longitude": 12.4922},
        )
        assert len(result) == 1

    async def test_reverse_level(self):
        location = await self.reverse_run(
            {"query": Point(41.8902, 12.4922), "level": "city"},
            {},
        )
        assert location.raw['type'] == 'city'

    async def test_reverse_radius(self):
        # The nearest address is about 140 m away.
        await self.reverse_run(
            {"query": Point(41.8902, 12.4922), "radius": 10},
            {},
            expect_failure=True,
        )

    async def test_reverse_annotations(self):
        location = await self.reverse_run(
            {"query": Point(41.8902, 12.4922), "annotations": True},
            {},
        )
        assert location.raw['timezone']['id'] == 'Europe/Rome'

    async def test_reverse_no_result(self):
        await self.reverse_run(
            # North Atlantic Ocean
            {"query": (35.173809, -37.485351)},
            {},
            expect_failure=True,
        )

    @pytest.mark.skipif("not pytz_available")
    async def test_reverse_timezone(self):
        timezone = await self.reverse_timezone_run(
            {"query": Point(-33.8688, 151.2093)},
            pytz.timezone("Australia/Sydney"),
        )
        assert timezone.raw['country_code'] == 'AU'

    @pytest.mark.skipif("not pytz_available")
    async def test_reverse_timezone_at_time(self):
        timezone = await self.reverse_timezone_run(
            {"query": "40.7537, -73.9849", "at_time": datetime(2010, 1, 1)},
            pytz.timezone("America/New_York"),
        )
        assert timezone.raw['timestamp'] == 1262304000
        assert timezone.raw['dst'] is False

    @pytest.mark.skipif("not pytz_available")
    async def test_reverse_timezone_at_sea(self):
        await self.reverse_timezone_run(
            {"query": (0, -30)},
            pytz.timezone("Etc/GMT+2"),
        )

    @pytest.mark.skipif("not pytz_available")
    async def test_reverse_timezone_invalid_at_time(self):
        with pytest.raises(GeocoderQueryError):
            self.geocoder.reverse_timezone((0, 0), at_time=0)

    async def test_invalid_key(self, disable_adapter_retries):
        async with self.inject_geocoder(MyGeocode(api_key='invalid')):
            with pytest.raises(GeocoderAuthenticationFailure) as cm:
                await self.geocode_run(
                    {"query": "Dam 1, Amsterdam"}, {}, skiptest_on_errors=False
                )
            assert str(cm.value) == "The API key is not valid."
