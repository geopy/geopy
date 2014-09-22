
import unittest

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
            {"query": u"\u6545\u5bab"},
            {"latitude": 30.90097, "longitude": 118.49436},
        )

    def test_reverse(self):
        """
        GeoNames.reverse
        """
        # work around ConfigurationError raised in GeoNames init
        self.geocoder = GeoNames(username=env['GEONAMES_USERNAME'])
        self.reverse_run(
            {"query": u"40.75376406311989, -73.98489005863667"},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )
