from unittest.mock import patch

import geopy.geocoders
from geopy.geocoders import LiveAddress
from test.geocoders.util import BaseTestGeocoder, env


class TestUnitLiveAddress:
    dummy_id = 'DUMMY12345'
    dummy_token = 'DUMMY67890'

    def test_user_agent_custom(self):
        geocoder = LiveAddress(
            auth_id=self.dummy_id,
            auth_token=self.dummy_token,
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    @patch.object(geopy.geocoders.options, 'default_scheme', 'http')
    def test_default_scheme_is_ignored(self):
        geocoder = LiveAddress(auth_id=self.dummy_id, auth_token=self.dummy_token)
        assert geocoder.scheme == 'https'


class TestLiveAddress(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return LiveAddress(
            auth_id=env['LIVESTREETS_AUTH_ID'],
            auth_token=env['LIVESTREETS_AUTH_TOKEN'],
            **kwargs
        )

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )
