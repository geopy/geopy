# coding: utf-8
from __future__ import unicode_literals
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
            {'raw': {"metaDataProperty":{"GeocoderMetaData":{"kind":"street","text":"Україна, Донецьк, площа Леніна","precision":"street","AddressDetails":{"Country":{"AddressLine":"Донецьк, площа Леніна","CountryNameCode":"UA","CountryName":"Україна","AdministrativeArea":{"AdministrativeAreaName":"Донецька область","SubAdministrativeArea":{"SubAdministrativeAreaName":"Донецька міська рада","Locality":{"LocalityName":"Донецьк","Thoroughfare":{"ThoroughfareName":"площа Леніна"}}}}}}}},"description":"Донецьк, Україна","name":"площа Леніна","boundedBy":{"Envelope":{"lowerCorner":"37.804575 48.001669","upperCorner":"37.805805 48.002538"}},"Point":{"pos":"37.805186 48.002104"}}},
        )
