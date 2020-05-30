import unittest

import pytest

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
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    def test_unicode_name(self):
        self.geocode_run(
            {"query": "площадь Ленина Донецк"},
            {"latitude": 48.002104, "longitude": 37.805186},
        )

    def test_failure_with_invalid_api_key(self):
        self.geocoder = Yandex(
            api_key='bad key'
        )
        with pytest.raises(GeocoderInsufficientPrivileges):
            self.geocode_run(
                {"query": "площадь Ленина Донецк"},
                {}
            )

    def test_reverse(self):
        self.reverse_run(
            {"query": "40.75376406311989, -73.98489005863667"},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    def test_geocode_lang(self):
        self.geocode_run(
            {"query": "площа Леніна Донецьк", "lang": "uk_UA"},
            {"address": "площа Леніна, Донецьк, Україна",
             "latitude": 48.002104, "longitude": 37.805186},
        )

    def test_reverse_kind(self):
        self.reverse_run(
            {"query": (55.743659, 37.408055), "kind": "locality"},
            {"address": "Москва, Россия"}
        )

    def test_reverse_lang(self):
        self.reverse_run(
            {"query": (55.743659, 37.408055), "kind": "locality",
             "lang": "uk_UA"},
            {"address": "Москва, Росія"}
        )
