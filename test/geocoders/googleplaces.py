
from geopy.compat import u
from geopy.point import Point
from geopy.geocoders import GooglePlaces
from test.geocoders.util import GeocoderTestBase, env


class GooglePlacesTestCase(GeocoderTestBase):  # pylint: disable=R0904,C0111

    @classmethod
    def setUpClass(cls):
        cls.geocoder = GooglePlaces(api_key=env['GOOGLEMAPS_KEY'])
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
            {"latitude": 25.1023554, "longitude": 121.5484925},
        )

    def test_geocode_language_parameter(self):
        """
        GooglePlaces.geocode using `language`
        """
        results_geocode = self._make_request(
            self.geocoder.geocode,
            self.known_country_fr,
            language="it",
        )

        address_components = results_geocode[0].raw['address_components']

        for component in address_components:
                for type in component['types']:
                   if "country" in type:
                    country = component['long_name']
                    self.assertEqual(country,self.known_country_it)

