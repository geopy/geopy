import warnings

import pytest

from geopy import exc
from geopy.geocoders import Here, HereV7
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


class TestUnitHere:

    def test_user_agent_custom(self):
        geocoder = Here(
            apikey='DUMMYKEY1234',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    def test_error_with_no_keys(self):
        with pytest.raises(exc.ConfigurationError):
            Here()

    def test_warning_with_legacy_auth(self):
        with warnings.catch_warnings(record=True) as w:
            Here(
                app_id='DUMMYID1234',
                app_code='DUMMYCODE1234',
            )
        assert len(w) == 1

    def test_no_warning_with_apikey(self):
        with warnings.catch_warnings(record=True) as w:
            Here(
                apikey='DUMMYKEY1234',
            )
        assert len(w) == 0


class BaseTestHere(BaseTestGeocoder):

    async def test_geocode_empty_result(self):
        await self.geocode_run(
            {"query": "xqj37"},
            {},
            expect_failure=True
        )

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624}
        )

    async def test_geocode_structured(self):
        query = {
            "street": "north michigan ave",
            "housenumber": "435",
            "city": "chicago",
            "state": "il",
            "postalcode": 60611,
            "country": "usa"
        }
        await self.geocode_run(
            {"query": query},
            {"latitude": 41.890, "longitude": -87.624}
        )

    async def test_geocode_unicode_name(self):
        # unicode in Japanese for Paris. (POIs not included.)
        await self.geocode_run(
            {"query": "\u30d1\u30ea"},
            {"latitude": 48.85718, "longitude": 2.34141}
        )

    async def test_bbox(self):
        await self.geocode_run(
            {"query": "moscow",  # Idaho USA
             "bbox": [[50.1, -130.1], [44.1, -100.9]]},
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )

    async def test_mapview(self):
        await self.geocode_run(
            {"query": "moscow",  # Idaho USA
             "mapview": [[50.1, -130.1], [44.1, -100.9]]},
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )

    async def test_geocode_shapes(self):
        address_string = "435 north michigan ave, chicago il 60611 usa"
        res = await self.geocode_run(
            {"query": address_string, "additional_data": "IncludeShapeLevel,postalCode"},
            {"latitude": 41.89035, "longitude": -87.62333},
        )
        shape_value = res.raw['Location']['Shape']['Value']
        assert shape_value.startswith('MULTIPOLYGON (((')

    async def test_geocode_with_language_de(self):
        address_string = "435 north michigan ave, chicago il 60611 usa"
        res = await self.geocode_run(
            {"query": address_string, "language": "de-DE"},
            {}
        )
        assert "Vereinigte Staaten" in res.address

    async def test_geocode_with_language_en(self):
        address_string = "435 north michigan ave, chicago il 60611 usa"
        res = await self.geocode_run(
            {"query": address_string, "language": "en-US"},
            {}
        )
        assert "United States" in res.address

    async def test_geocode_with_paging(self):
        address_string = "Hauptstr., Berlin, Germany"
        input = {"query": address_string, "maxresults": 12, "exactly_one": False}
        res = await self.geocode_run(input, {})
        assert len(res) == 12

        input["pageinformation"] = 2
        res = await self.geocode_run(input, {})
        assert len(res) >= 3
        assert len(res) <= 6

        input["pageinformation"] = 3
        res = await self.geocode_run(input, {}, expect_failure=True)

    async def test_reverse(self):
        await self.reverse_run(
            {"query": Point(40.753898, -73.985071)},
            {"latitude": 40.753898, "longitude": -73.985071}
        )

    async def test_reverse_point_radius_1000_float(self):
        # needs more testing
        res = await self.reverse_run(
            {"query": Point(40.753898, -73.985071), "radius": 1000.12,
             "exactly_one": False},
            {"latitude": 40.753898, "longitude": -73.985071}
        )
        assert len(res) > 5

    async def test_reverse_point_radius_10(self):
        # needs more testing
        res = await self.reverse_run(
            {"query": Point(40.753898, -73.985071), "radius": 10, "exactly_one": False},
            {"latitude": 40.753898, "longitude": -73.985071}
        )
        assert len(res) > 5

    async def test_reverse_with_language_de(self):
        res = await self.reverse_run(
            {"query": Point(40.753898, -73.985071), "language": "de-DE"},
            {}
        )
        assert "Vereinigte Staaten" in res.address

    async def test_reverse_with_language_en(self):
        res = await self.reverse_run(
            {"query": Point(40.753898, -73.985071), "language": "en-US"},
            {}
        )
        assert "United States" in res.address

    async def test_reverse_with_mode_areas(self):
        res = await self.reverse_run(
            {"query": Point(40.753898, -73.985071), "mode": "retrieveAreas"},
            {}
        )
        assert "Theater District-Times Square" in res.address

    async def test_reverse_with_maxresults_5(self):
        res = await self.reverse_run(
            {
                "query": Point(40.753898, -73.985071),
                "maxresults": 5,
                "exactly_one": False
            },
            {}
        )
        assert len(res) == 5


class TestHereApiKey(BaseTestHere):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return Here(
            apikey=env['HERE_APIKEY'],
            timeout=10,
            **kwargs
        )


class TestHereLegacyAuth(BaseTestHere):

    @classmethod
    def make_geocoder(cls, **kwargs):
        with warnings.catch_warnings(record=True) as w:
            geocoder = Here(
                app_id=env['HERE_APP_ID'],
                app_code=env['HERE_APP_CODE'],
                timeout=10,
                **kwargs
            )
        assert len(w) == 1
        return geocoder


class TestHereV7(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return HereV7(env['HERE_APIKEY'], **kwargs)

    async def test_geocode_empty_result(self):
        await self.geocode_run(
            {"query": "xqj37"},
            {},
            expect_failure=True
        )

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624}
        )

    async def test_geocode_query_and_components(self):
        query = "435 north michigan ave"
        components = {
            "city": "chicago",
            "state": "il",
            "postalCode": 60611,
            "country": "usa",
        }
        await self.geocode_run(
            {"query": query, "components": components},
            {"latitude": 41.890, "longitude": -87.624}
        )

    async def test_geocode_structured(self):
        components = {
            "street": "north michigan ave",
            "houseNumber": "435",
            "city": "chicago",
            "state": "il",
            "postalCode": 60611,
            "country": "usa",
        }
        await self.geocode_run(
            {"components": components},
            {"latitude": 41.890, "longitude": -87.624}
        )

    async def test_geocode_unicode_name(self):
        # unicode in Japanese for Paris. (POIs not included.)
        await self.geocode_run(
            {"query": "\u30d1\u30ea"},
            {"latitude": 48.85718, "longitude": 2.34141}
        )

    async def test_geocode_at(self):
        await self.geocode_run(
            {
                "query": "moscow",  # Idaho USA
                "at": (46.734303, -116.999558)
            },
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )

    async def test_geocode_countries(self):
        await self.geocode_run(
            {
                "query": "moscow",  # Idaho USA
                "countries": ["USA", "CAN"],
            },
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )

    async def test_geocode_language(self):
        address_string = "435 north michigan ave, chicago il 60611 usa"
        res = await self.geocode_run(
            {"query": address_string, "language": "de-DE"},
            {}
        )
        assert "Vereinigte Staaten" in res.address

        res = await self.geocode_run(
            {"query": address_string, "language": "en-US"},
            {}
        )
        assert "United States" in res.address

    async def test_geocode_limit(self):
        res = await self.geocode_run(
            {
                "query": "maple street",
                "limit": 5,
                "exactly_one": False
            },
            {}
        )
        assert len(res) == 5

    async def test_reverse(self):
        await self.reverse_run(
            {"query": Point(40.753898, -73.985071)},
            {"latitude": 40.753898, "longitude": -73.985071}
        )

    async def test_reverse_language(self):
        res = await self.reverse_run(
            {"query": Point(40.753898, -73.985071), "language": "de-DE"},
            {}
        )
        assert "Vereinigte Staaten" in res.address

        res = await self.reverse_run(
            {"query": Point(40.753898, -73.985071), "language": "en-US"},
            {}
        )
        assert "United States" in res.address

    async def test_reverse_limit(self):
        res = await self.reverse_run(
            {
                "query": Point(40.753898, -73.985071),
                "limit": 5,
                "exactly_one": False
            },
            {}
        )
        assert len(res) == 5
