# -*- coding: utf-8 -*-

import base64
from geopy.compat import u
from geopy.point import Point
from geopy.geocoders import GooglePlaces
from test.geocoders.util import GeocoderTestBase, env
from geopy.compat import u, urlparse, parse_qs

class GooglePlacesTestCase(GeocoderTestBase):  # pylint: disable=R0904,C0111

    @classmethod
    def setUpClass(cls):
        cls.geocoder = GooglePlaces(api_key=env['GOOGLEMAPS_KEY'], timeout=50)
        cls.known_country_ar = "فرنسا"
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
            language="ar",
        )

        address_components = results_geocode[0].raw['address_components']

        for component in address_components:
            for type in component['types']:
                if "country" in type:
                    country = component['long_name']
                    self.assertEqual(country.encode('utf-8'),self.known_country_ar)


    def test_get_signed_url_with_channel(self):
        """
        GooglePlaces._get_signed_url
        """
        geocoder = GooglePlaces(
            client_id='my_client_id',
            secret_key=base64.urlsafe_b64encode('my_secret_key'.encode('utf8')),
            channel='my_channel'
        )

        signed_url = geocoder._get_signed_url('/maps/api/autocomplete/json',{'address': '1 5th Ave New York, NY'})
        params = parse_qs(urlparse(signed_url).query)

        self.assertTrue('channel' in params)
        self.assertTrue('signature' in params)
        self.assertTrue('client' in params)