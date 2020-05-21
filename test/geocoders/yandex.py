# coding: utf-8
from __future__ import unicode_literals

import unittest
import warnings

from geopy.exc import GeocoderInsufficientPrivileges
from geopy.geocoders import Yandex
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(
    bool(env['YANDEX_KEY']),
    "No YANDEX_KEY env variable set"
)
class YandexTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.delta = 0.04
        cls.geocoder = Yandex(api_key=env.get('YANDEX_KEY'))

    def test_user_agent_custom(self):
        geocoder = Yandex(
            api_key='mock',
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_warning_with_no_api_key(self):
        """
        Yandex warns if no API key is present
        """
        with warnings.catch_warnings(record=True) as w:
            Yandex()
        self.assertEqual(len(w), 1)

    def test_unicode_name(self):
        """
        Yandex.geocode unicode
        """
        self.geocode_run(
            {"query": "площадь Ленина Донецк"},
            {"latitude": 48.002104, "longitude": 37.805186},
        )

    def test_failure_with_invalid_api_key(self):
        """
        Yandex.geocode with incorrect api_key
        """
        self.geocoder = Yandex(
            api_key='bad key'
        )
        with self.assertRaises(GeocoderInsufficientPrivileges):
            self.geocode_run(
                {"query": "площадь Ленина Донецк"},
                {}
            )

    def test_reverse(self):
        """
        Yandex.reverse
        """
        self.reverse_run(
            {"query": "40.75376406311989, -73.98489005863667", "exactly_one": True},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    def test_params(self):
        """
        Yandex.geocode with lang
        """
        self.geocode_run(
            {"query": "площа Леніна Донецьк", "lang": "uk_UA"},
            {"address": "площа Леніна, Донецьк, Україна",
             "latitude": 48.002104, "longitude": 37.805186},
        )

    def test_reverse_kind_param(self):
        self.reverse_run(
            {"query": (55.743659, 37.408055), "kind": "locality", "exactly_one": True},
            {"address": "Москва, Россия"}
        )

    def test_reverse_lang_param(self):
        self.reverse_run(
            {"query": (55.743659, 37.408055), "kind": "locality",
             "lang": "uk_UA", "exactly_one": True},
            {"address": "Москва, Росія"}
        )
