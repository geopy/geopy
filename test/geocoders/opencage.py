import pytest

from geopy.geocoders import OpenCage
from test.geocoders.util import BaseTestGeocoder, env


class TestUnitOpenCage:

    def test_user_agent_custom(self):
        geocoder = OpenCage(
            api_key='DUMMYKEY1234',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'


@pytest.mark.skipif(
    not bool(env.get('OPENCAGE_KEY')),
    reason="No OPENCAGE_KEY env variables set"
)
class TestOpenCage(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return OpenCage(
            api_key=env['OPENCAGE_KEY'],
            timeout=10,
            **kwargs
        )

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    async def test_unicode_name(self):
        await self.geocode_run(
            {"query": "\u6545\u5bab"},
            {"latitude": 39.916, "longitude": 116.390},
        )

    async def test_geocode_empty_result(self):
        await self.geocode_run(
            {"query": "xqj37"},
            {},
            expect_failure=True
        )

    async def test_bounds(self):
        await self.geocode_run(
            {"query": "moscow",  # Idaho USA
             "bounds": [[50.1, -130.1], [44.1, -100.9]]},
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )

    async def test_country_str(self):
        await self.geocode_run(
            {"query": "kazan",
             "country": 'tr'},
            {"latitude": 40.2317, "longitude": 32.6839},
        )

    async def test_country_list(self):
        await self.geocode_run(
            {"query": "kazan",
             "country": ['cn', 'tr']},
            {"latitude": 40.2317, "longitude": 32.6839},
        )
