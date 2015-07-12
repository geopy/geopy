# -*- coding: UTF-8 -*-
import unittest2 as unittest

from geopy.compat import u
from geopy.geocoders import GeoNames
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(  # pylint: disable=R0904,C0111
    bool(env.get('GEONAMES_USERNAME')),
    "No GEONAMES_USERNAME env variable set"
)
class GeoNamesTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.delta = 0.04

    def test_unicode_name(self):
        """
        GeoNames.geocode unicode
        """
        # work around ConfigurationError raised in GeoNames init
        self.geocoder = GeoNames(username=env['GEONAMES_USERNAME'])
        self.geocode_run(
            {"query": "Mount Everest, Nepal"},
            {"latitude": 27.987, "longitude": 86.925},
        )

    def test_reverse(self):
        """
        GeoNames.reverse
        """
        # work around ConfigurationError raised in GeoNames init
        self.geocoder = GeoNames(username=env['GEONAMES_USERNAME'])
        self.reverse_run(
            {"query": "40.75376406311989, -73.98489005863667"},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )
