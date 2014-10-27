# coding: utf-8
import unittest

from geopy.geocoders import Yandex
from test.geocoders.util import GeocoderTestBase


class YandexTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.delta = 0.04

    def test_unicode_name(self):
        """
        Yandex.geocode unicode
        """
        self.geocoder = Yandex()
        self.geocode_run(
            {"query": u"улица Ленина Донецк"},
            {"latitude": 47.922033, "longitude": 37.579717},
        )

    def test_reverse(self):
        """
        Yandex.reverse
        """
        self.geocoder = Yandex()
        self.reverse_run(
            {"query": u"40.75376406311989, -73.98489005863667"},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )
