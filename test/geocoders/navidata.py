# -*- coding: UTF-8 -*-
import unittest

from geopy.compat import u
from geopy.geocoders import NaviData
from test.geocoders.util import GeocoderTestBase, env



class NaviDataTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.delta = 0.04

    def test_unicode_name(self):
        """
        NaviData.geocode unicode
        """

        self.geocoder = NaviData()
        self.geocode_run(
            {"query": "Warszawa, mazowieckie"},
            {"latitude": 52.231, "longitude": 21.006},
        )


    def test_api_key(self):
        """
        NaviData.geocode - test API key parameter. Given API key is bogus - but invalid keys are silently discarded by geocoding service so
        for testing purposes this is fine
        """

        self.geocoder = NaviData(api_key='geopy_test')
        self.geocode_run(
            {"query": "Warszawa, mazowieckie"},
            {"latitude": 52.231, "longitude": 21.006},
        )

    def test_reverse(self):
        """
        NaviData.reverse
        """

        self.geocoder = NaviData()
        self.reverse_run(
            {"query": "51.036963, 16.755802"},
            {"latitude": 51.036963, "longitude": 16.755802},
        )
