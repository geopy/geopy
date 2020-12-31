from geopy.geocoders import BANFrance
from test.geocoders.util import BaseTestGeocoder


class TestBANFrance(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return BANFrance(timeout=10, **kwargs)

    async def test_user_agent_custom(self):
        geocoder = BANFrance(
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    async def test_geocode_with_address(self):
        location = await self.geocode_run(
            {"query": "Camp des Landes, 41200 VILLEFRANCHE-SUR-CHER"},
            {"latitude": 47.293048, "longitude": 1.718985},
        )
        assert "Camp des Landes" in location.address

    async def test_reverse(self):
        location = await self.reverse_run(
            {"query": "48.154587,3.221237"},
            {"latitude": 48.154587, "longitude": 3.221237},
        )
        assert "Collemiers" in location.address

    async def test_geocode_limit(self):
        result = await self.geocode_run(
            {"query": "8 bd du port", "limit": 2, "exactly_one": False},
            {}
        )
        assert 2 >= len(result)
