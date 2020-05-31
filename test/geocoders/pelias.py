# coding: utf8
from __future__ import unicode_literals

import unittest
import warnings
from abc import ABCMeta, abstractmethod

from six import with_metaclass

from geopy.geocoders import Pelias
from geopy.point import Point
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

    def test_reverse(self):
        self.reverse_run(
            {"query": Point(40.75376406311989, -73.98489005863667)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667}
        )

    def test_boundary_rect(self):
        self.geocode_run(
            {"query": "moscow",  # Idaho USA
             "boundary_rect": [[50.1, -130.1], [44.1, -100.9]]},
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )

    def test_boundary_rect_deprecated(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            self.geocode_run(
                {"query": "moscow",  # Idaho USA
                 "boundary_rect": [-130.1, 44.1, -100.9, 50.1]},
                {"latitude": 46.7323875, "longitude": -117.0001651},
            )
            assert 1 == len(w)

    def test_geocode_language_parameter(self):
        query = "Graben 7, Wien"
        result_geocode = self.geocode_run(
            {"query": query, "language": "de"}, {}
        )
        assert result_geocode.raw['properties']['country'] == "Österreich"

        result_geocode = self.geocode_run(
            {"query": query, "language": "en"}, {}
        )
        assert result_geocode.raw['properties']['country'] == "Austria"

    def test_reverse_language_parameter(self):
        query = "48.198674, 16.348388"
        result_reverse_de = self.reverse_run(
            {"query": query, "exactly_one": True, "language": "de"},
            {},
        )
        assert result_reverse_de.raw['properties']['country'] == "Österreich"

        result_reverse_en = self.reverse_run(
            {"query": query, "exactly_one": True, "language": "en"},
            {},
        )
        assert result_reverse_en.raw['properties']['country'] == "Austria"


@unittest.skipUnless(
    bool(env.get('PELIAS_DOMAIN')),
    "No PELIAS_DOMAIN env variable set"
)
class PeliasTestCase(BasePeliasTestCase, GeocoderTestBase):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return Pelias(env.get('PELIAS_DOMAIN'), api_key=env.get('PELIAS_KEY'),
                      **kwargs)
