# coding: utf8
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass
import unittest

from geopy.point import Point
from geopy.geocoders import Pelias
from test.geocoders.util import GeocoderTestBase, env


class BasePeliasTestCase(with_metaclass(ABCMeta, object)):

    delta = 0.04

    @classmethod
    @abstractmethod
    def make_geocoder(cls, **kwargs):
        pass

    @classmethod
    def setUpClass(cls):
        cls.geocoder = cls.make_geocoder()

        cls.known_state_de = "Verwaltungsregion Ionische Inseln"
        cls.known_state_en = "Ionian Islands Periphery"

    def test_geocode(self):
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        self.geocode_run(
            {"query": "san josé california"},
            {"latitude": 37.33939, "longitude": -121.89496},
        )

    def test_reverse_string(self):
        self.reverse_run(
            {"query": "40.75376406311989, -73.98489005863667"},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667}
        )

    def test_reverse_point(self):
        self.reverse_run(
            {"query": Point(40.75376406311989, -73.98489005863667)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667}
        )


@unittest.skipUnless(
    bool(env.get('PELIAS_DOMAIN')),
    "No PELIAS_DOMAIN env variable set"
)
class PeliasTestCase(BasePeliasTestCase, GeocoderTestBase):

    def make_geocoder(cls, **kwargs):
        return Pelias(env.get('PELIAS_DOMAIN'), api_key=env.get('PELIAS_KEY'),
                      **kwargs)
