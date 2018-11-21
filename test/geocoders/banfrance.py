# coding: utf8
from __future__ import unicode_literals

import unittest
import warnings
from abc import ABCMeta, abstractmethod

from six import with_metaclass

from geopy.geocoders import banfrance
from geopy.point import Point
from test.geocoders.util import GeocoderTestBase, env


class BaseBANFranceTestCase(with_metaclass(ABCMeta, object)):

    delta = 0.04

    @classmethod
    @abstractmethod
    def make_geocoder(cls, **kwargs):
        pass

    @classmethod
    def setUpClass(cls):
        cls.geocoder = cls.make_geocoder()


    def test_geocode_with_address(self):
        """
        BANFrance.geocode Address
        """
        self.geocode_run(
            {"query": "Camp des Landes, 41200 VILLEFRANCHE-SUR-CHER"},
            {"latitude": 47.293048,
                "longitude": 1.718985,
                "address": "Le Camp des Landes 41200 Villefranche-sur-Cher"},
        )

    def test_reverse(self):
        """
        BANFrance.reverse simple
        """
        res = self.reverse_run(
            {"query": '47.229554,-1.541519',
                "exactly_one": True},
            {},
        )
        self.assertEqual(
            res.address,
            '7 Avenue Camille Guérin 44000 Nantes'
        )



class BANFranceTestCase(BaseBANFranceTestCase, GeocoderTestBase):

    @classmethod
    def make_geocoder(cls, **kwargs):
        kwargs.setdefault('user_agent', 'geopy-test')
        return banfrance.BANFrance(**kwargs)

    # def test_default_user_agent_warning(self):
    #     with warnings.catch_warnings(record=True) as w:
    #         warnings.simplefilter('always')
    #         banfrance.BANFrance()
    #         self.assertEqual(1, len(w))

    #     with warnings.catch_warnings(record=True) as w:
    #         warnings.simplefilter('always')
    #         banfrance.BANFrance(user_agent='my_application')
    #         self.assertEqual(0, len(w))

    #     with warnings.catch_warnings(record=True) as w:
    #         warnings.simplefilter('always')
    #         with patch.object(geopy.geocoders.options, 'default_user_agent',
    #                           'my_application'):
    #             banfrance.BANFrance()
    #         self.assertEqual(0, len(w))