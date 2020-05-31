# coding: utf8
from __future__ import unicode_literals

from geopy.geocoders import Photon
from geopy.point import Point
from test.geocoders.util import GeocoderTestBase


class PhotonTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Photon()
        cls.known_country_de = "Frankreich"
        cls.known_country_fr = "France"

    def test_user_agent_custom(self):
        geocoder = Photon(
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    def test_geocode(self):
        location = self.geocode_run(
            {"query": "14 rue pelisson villeurbanne"},
            {"latitude": 45.7733963, "longitude": 4.88612369},
        )
        assert "France" in location.address

    def test_osm_tag(self):
        self.geocode_run(
            {"query": "Freedom", "osm_tag": "place"},
            {"latitude": 44.3862491, "longitude": -88.290994},
        )

        self.geocode_run(
            {"query": "Freedom", "osm_tag": ["!place", "tourism"]},
            {"latitude": 38.8898061, "longitude": -77.009088},
        )

    def test_unicode_name(self):
        self.geocode_run(
            {"query": "\u6545\u5bab"},
            {"latitude": 39.916, "longitude": 116.390},
        )

    def test_reverse(self):
        result = self.reverse_run(
            {"query": Point(45.7733105, 4.8869339)},
            {"latitude": 45.7733105, "longitude": 4.8869339}
        )
        assert "France" in result.address

    def test_geocode_language_parameter(self):
        result_geocode = self.geocode_run(
            {"query": self.known_country_fr, "language": "de"},
            {},
        )
        assert (
            result_geocode.raw['properties']['country'] ==
            self.known_country_de
        )

    def test_reverse_language_parameter(self):

        result_reverse_it = self.reverse_run(
            {"query": "45.7733105, 4.8869339",
             "exactly_one": True,
             "language": "de"},
            {},
        )
        assert (
            result_reverse_it.raw['properties']['country'] ==
            self.known_country_de
        )

        result_reverse_fr = self.reverse_run(
            {"query": "45.7733105, 4.8869339",
             "exactly_one": True,
             "language": "fr"},
            {},
        )
        assert (
            result_reverse_fr.raw['properties']['country'] ==
            self.known_country_fr
        )
