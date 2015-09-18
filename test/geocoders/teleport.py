# -*- coding: UTF-8 -*-
from geopy.geocoders import Teleport
from test.geocoders.util import GeocoderTestBase


class TeleportTestCaseUnitTest(GeocoderTestBase):

    def test_user_agent_custom(self):
        geocoder = Teleport(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')


class TeleportTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.delta = 0.04

    def test_unicode_name(self):
        """
        Teleport.geocode unicode
        """
        # work around ConfigurationError raised in GeoNames init
        self.geocoder = Teleport()
        self.geocode_run(
            {"query": "New York, NY"},
            {"latitude": 40.71427, "longitude": -74.00597},
        )

    def test_reverse(self):
        """
        Teleport.reverse
        """
        # work around ConfigurationError raised in GeoNames init
        self.geocoder = Teleport()
        self.reverse_run(
            {"query": "40.71427, -74.00597"},
            {"latitude": 40.71427, "longitude": -74.00597,
             "address": "New York City, New York, United States"},
        )
