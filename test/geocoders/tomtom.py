# coding: utf-8
from __future__ import unicode_literals

import unittest
from abc import ABCMeta, abstractmethod

from six import with_metaclass

from geopy.geocoders import TomTom
from test.geocoders.util import GeocoderTestBase, env


class BaseTomTomTestCase(with_metaclass(ABCMeta, object)):

    @classmethod
    @abstractmethod
    def make_geocoder(cls, **kwargs):
        pass

    @classmethod
    def setUpClass(cls):
        cls.geocoder = cls.make_geocoder()

    def test_user_agent_custom(self):
        geocoder = self.make_geocoder(
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    def test_geocode(self):
        location = self.geocode_run(
            {'query': 'москва'},
            {'latitude': 55.75587, 'longitude': 37.61768},
        )
        assert 'Москва' in location.address

    def test_reverse(self):
        location = self.reverse_run(
            {'query': '51.5285057, -0.1369635', 'language': 'en-US'},
            {'latitude': 51.5285057, 'longitude': -0.1369635,
             "delta": 0.3},
        )
        assert 'London' in location.address
        # Russian Moscow address can be reported differently, so
        # we're querying something more ordinary, like London.
        #
        # For example, AzureMaps might return
        # `Красная площадь, 109012 Moskva` instead of the expected
        # `Красная площадь, 109012 Москва`, even when language is
        # specified explicitly as `ru-RU`. And TomTom always returns
        # the cyrillic variant, even when the `en-US` language is
        # requested.

    def test_geocode_empty(self):
        self.geocode_run(
            {'query': 'sldkfhdskjfhsdkhgflaskjgf'},
            {},
            expect_failure=True,
        )


@unittest.skipUnless(
    bool(env.get('TOMTOM_KEY')),
    "No TOMTOM_KEY env variable set"
)
class TomTomTestCase(BaseTomTomTestCase, GeocoderTestBase):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return TomTom(env['TOMTOM_KEY'], timeout=3,
                      **kwargs)
