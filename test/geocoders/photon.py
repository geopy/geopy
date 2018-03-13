# coding: utf8
from __future__ import unicode_literals

from geopy.compat import u
from geopy.point import Point
from geopy.geocoders import Photon
from test.geocoders.util import GeocoderTestBase


class PhotonTestCase(GeocoderTestBase):  # pylint: disable=R0904,C0111

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Photon()
        cls.known_country_it = "Francia"
        cls.known_country_fr = "France"

    def test_user_agent_custom(self):
        geocoder = Photon(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_geocode(self):
        """
        Photon.geocode
        """
        self.geocode_run(
            {"query": "14 rue pelisson villeurbanne"},
            {"address": "Rue du 14 Juillet 1789, 69003, Villeurbanne, Auvergne-Rhône-Alpes, France",
             "latitude": 45.7733963, "longitude": 4.88612369},
        )

    def test_osm_tag(self):
        """
        Photon.geocode osm_tag
        """
        self.geocode_run(
            {"query": "Freedom", "osm_tag": "place"},
            {"latitude": 44.3862491, "longitude": -88.290994},
        )

        self.geocode_run(
            {"query": "Freedom", "osm_tag": ["!place", "tourism"]},
            {"latitude": 38.8898061, "longitude": -77.009088},
        )

    def test_unicode_name(self):
        """
        Photon.geocode unicode
        """
        self.geocode_run(
            {"query": "\u6545\u5bab"},
            {"latitude": 39.916, "longitude": 116.390},
        )

    def test_reverse_string(self):
        """
        Photon.reverse string
        """
        self.reverse_run(
            {"query": "45.7733105, 4.8869339"},
            {"latitude": 45.7733105, "longitude": 4.8869339}
        )

    def test_reverse_point(self):
        """
        Photon.reverse Point
        """
        self.reverse_run(
            {"query": Point(45.7733105, 4.8869339)},
            {"address": "Rue Raspail, 69100, Villeurbanne, Auvergne-Rhône-Alpes, France",
             "latitude": 45.7733105, "longitude": 4.8869339}
        )

    def test_geocode_language_parameter(self):
        """
        Photon.geocode using `language`
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

    def test_reverse_language_parameter(self):
        """
        Photon.reverse using `language`
        """
        result_reverse_it = self._make_request(
            self.geocoder.reverse,
            "45.7733105, 4.8869339",
            exactly_one=True,
            language="it",
        )
        self.assertEqual(
            result_reverse_it.raw['properties']['country'],
            self.known_country_it
        )

        result_reverse_fr = self._make_request(
            self.geocoder.reverse,
            "45.7733105, 4.8869339",
            exactly_one=True,
            language="fr"
        )
        self.assertEqual(
            result_reverse_fr.raw['properties']['country'],
            self.known_country_fr
        )
