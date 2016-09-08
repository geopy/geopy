
from geopy.compat import u
from geopy.point import Point
from geopy.geocoders import GooglePlaces
from test.geocoders.util import GeocoderTestBase


class GooglePlacesTestCase(GeocoderTestBase):  # pylint: disable=R0904,C0111

    @classmethod
    def setUpClass(cls):
        cls.geocoder = GooglePlaces()
        cls.known_country_it = "Francia"
        cls.known_country_fr = "France"

    def test_geocode(self):
        """
        GooglePlaces.geocode
        """
        self.geocode_run(
            {"query": "14 rue pelisson villeurbanne"},
            {"latitude": 45.7733963, "longitude": 4.88612369},
        )

    def test_unicode_name(self):
        """
        GooglePlaces.geocode unicode
        """
        self.geocode_run(
            {"query": u("\u6545\u5bab")},
            {"latitude": 39.916, "longitude": 116.390},
        )

    def test_geocode_language_parameter(self):
        """
        GooglePlaces.geocode using `language`
        """
        result_geocode = self._make_request(
            self.geocoder.geocode,
            self.known_country_fr,
            language="it",
        )
        self.assertEqual(
            result_geocode.raw['properties']['country'],
            self.known_country_it
        )

