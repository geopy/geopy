# coding: utf8
from __future__ import unicode_literals

from mock import patch
from geopy.compat import u
from geopy.point import Point
from geopy.geocoders import Mapzen
from test.geocoders.util import GeocoderTestBase


class MapzenTestCase(GeocoderTestBase): # pylint: disable=R0904,C0111

    delta = 0.04

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Mapzen('search-W5SkZLU')
        cls.known_state_de = "Verwaltungsregion Ionische Inseln"
        cls.known_state_en = "Ionian Islands Periphery"

    def test_geocode(self):
        """
        Mapzen.geocode
        """
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        """
        Mapzen.geocode unicode
        """
        self.geocode_run(
            {"query": u(u'san josé california'.encode('utf8'))},
            {"latitude": 37.33939, "longitude": -121.89496},
        )

    def test_reverse_string(self):
        """
        Mapzen.reverse string
        """
        self.reverse_run(
            {"query": "40.75376406311989, -73.98489005863667"},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667}
        )

    def test_reverse_point(self):
        """
        Mapzen.reverse Point
        """
        self.reverse_run(
            {"query": Point(40.75376406311989, -73.98489005863667)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667}
        )
