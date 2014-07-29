
import unittest

from geopy.geocoders import GeoNames
from test.geocoders.util import GeocoderTestBase, env

@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['GEONAMES_USERNAME'] is not None,
    "No GEONAMES_USERNAME env variable set"
)
class GeoNamesTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = GeoNames(username=env['GEONAMES_USERNAME'])
        cls.delta = 0.04

    def test_unicode_name(self):
        """
        GeoNames.geocode unicode
        """
        self.geocode_run(
            {"query": u"\u6545\u5bab"},
            {"latitude": 30.90097, "longitude": 118.49436},
        )


