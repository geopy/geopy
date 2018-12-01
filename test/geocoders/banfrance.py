from geopy.geocoders import BANFrance
from test.geocoders.util import GeocoderTestBase


class BANFranceTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = BANFrance(timeout=10)

    def test_user_agent_custom(self):
        geocoder = BANFrance(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_geocode_with_address(self):
        location = self.geocode_run(
            {"query": "Camp des Landes, 41200 VILLEFRANCHE-SUR-CHER"},
            {"latitude": 47.293048, "longitude": 1.718985},
        )
        self.assertIn("Camp des Landes", location.address)

    def test_reverse(self):
        location = self.reverse_run(
            {"query": "48.154587,3.221237", "exactly_one": True},
            {"latitude": 48.154587, "longitude": 3.221237},
        )
        self.assertIn("Rue des Fontaines", location.address)

    def test_geocode_limit(self):
        result = self.geocode_run(
            {"query": "8 bd du port", "limit": 2, "exactly_one": False},
            {}
        )
        self.assertGreaterEqual(2, len(result))
