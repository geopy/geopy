# -*- coding: UTF-8 -*-
import unittest

from geopy.compat import u
from geopy.geocoders import NaviData
from test.geocoders.util import GeocoderTestBase, env



class NaviDataTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.delta = 0.04

    def test_user_agent_custom(self):
        geocoder = NaviData(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_unicode_name(self):
        """
        NaviData.geocode unicode
        """
        self.geocoder = NaviData()
        self.geocode_run(
            {"query": "Warszawa, mazowieckie"},
            {"latitude": 52.231, "longitude": 21.006},
        )

    def test_unicode_name_exactly_one_false(self):
        """
        NaviData.geocode unicode
        """
        self.geocoder = NaviData()
        self.geocode_run(
            {"query": "Warszawa, mazowieckie", "exactly_one" : False},
            {"latitude": 52.231, "longitude": 21.006},
        )

    def test_api_key(self):
        """
        NaviData.geocode test API key parameter
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

    def test_reverse_with_api(self):
        """
        NaviData.reverse
        """
        self.geocoder = NaviData(api_key='geopy_test')
        self.reverse_run(
            {"query": "51.036963, 16.755802"},
            {"latitude": 51.036963, "longitude": 16.755802},
        )
