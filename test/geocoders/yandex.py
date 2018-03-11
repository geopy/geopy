# coding: utf-8
from __future__ import unicode_literals

from geopy.geocoders import Yandex
from test.geocoders.util import GeocoderTestBase


class YandexTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.delta = 0.04

    def test_user_agent_custom(self):
        geocoder = Yandex(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_unicode_name(self):
        """
        Yandex.geocode unicode
        """
        self.geocoder = Yandex()
        self.geocode_run(
            {"query": "площадь Ленина Донецк"},
            {"latitude": 48.002104, "longitude": 37.805186},
        )

    def test_reverse(self):
        """
        Yandex.reverse
        """
        self.geocoder = Yandex()
        self.reverse_run(
            {"query": "40.75376406311989, -73.98489005863667"},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    def test_params(self):
        """
        Yandex.geocode with api_key and lang set
        """
        self.geocoder = Yandex(
            api_key='AGg6X1QBAAAAk0ZiFwIAUfmxqDgGv6n7bhzuCl5D4MC31ZoAAAAAAAAAAADSboKTjoZyt88aQGXUGHUdJ3JHqQ==',
            lang='uk_UA'
        )
        self.geocode_run(
            {"query": "площа Леніна Донецьк"},
            {"address": "Донецьк, Україна", "latitude": 48.002104, "longitude": 37.805186},
        )
