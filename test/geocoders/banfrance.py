from geopy.geocoders import BANFrance
from test.geocoders.util import GeocoderTestBase


class BANFranceTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.delta = 0.04
        cls.geocoder = BANFrance(timeout=10)

    def test_user_agent_custom(self):
        geocoder = BANFrance(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_geocode_with_address(self):
        """
        banfrance.geocode Address
        """

        self.geocode_run(
            {"query": "Camp des Landes, 41200 VILLEFRANCHE-SUR-CHER"},
            {"latitude": 47.293048, "longitude": 1.718985,
             "address": "Le Camp des Landes 41200 Villefranche-sur-Cher"},
        )

    def test_reverse(self):
        """
        banfrance.reverse
        """

        self.reverse_run(
            {"query": "48.154587,3.221237", "exactly_one": True},
            {"latitude": 48.154587, "longitude": 3.221237},
            {"address": "15 Rue des Fontaines 89100 Collemiers"}
        )

    def test_limit(self):
        """
        banfrance.geocode limit
        """
        result = self.geocode_run(
            {"query": "8 bd du port", "limit": 2, "exactly_one": False},
            {}
        )
        self.assertGreaterEqual(2, len(result))
