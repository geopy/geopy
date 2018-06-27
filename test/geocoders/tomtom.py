# coding: utf-8
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass
import unittest

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
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_geocode(self):
        location = self.geocode_run(
            {'query': 'москва'},
            {'latitude': 55.75587, 'longitude': 37.61768},
        )
        self.assertIn('Москва', location.address)

    def test_reverse(self):
        location = self.reverse_run(
            {'query': '55.75587, 37.61768'},
            {'latitude': 55.75587, 'longitude': 37.61768},
        )
        self.assertIn('Москва', location.address)

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
