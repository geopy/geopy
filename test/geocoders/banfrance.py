from abc import ABCMeta, abstractmethod

from six import with_metaclass

from geopy.geocoders import banfrance
from test.geocoders.util import GeocoderTestBase


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
            {"query": '48.154587,3.221237',
                "exactly_one": True},
            {},
        )
        self.assertEqual(
            res.address,
            '15 Rue des Fontaines 89100 Collemiers'
        )


class BANFranceTestCase(BaseBANFranceTestCase, GeocoderTestBase):

    @classmethod
    def make_geocoder(cls, **kwargs):
        kwargs.setdefault('user_agent', 'geopy-test')
        return banfrance.BANFrance(**kwargs)
