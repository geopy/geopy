import warnings

import pytest

from geopy import exc
from geopy.geocoders import HereV7
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


class TestUnitHere:

    def test_user_agent_custom(self):
        geocoder = HereV7(
            apikey='DUMMYKEY1234',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    def test_error_with_no_keys(self):
        with pytest.raises(exc.ConfigurationError):
            HereV7()

    def test_no_warning_with_apikey(self):
        with warnings.catch_warnings(record=True) as w:
            HereV7(
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

    async def test_search_context(self):
        await self.geocode_run(
            {
                "query": "moscow",  # Idaho USA
                "at": (46.734303, -116.999558)
            },
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )

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

    async def test_reverse(self):
        await self.reverse_run(
            {"query": Point(40.753898, -73.985071)},
            {"latitude": 40.753898, "longitude": -73.985071}
        )

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


@pytest.mark.skipif(
    not bool(env.get('HERE_APIKEY')),
    reason="No HERE_APIKEY env variable set"
)
class TestHereApiKey(BaseTestHere):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return HereV7(
            apikey=env['HERE_APIKEY'],
            timeout=10,
            **kwargs
        )
