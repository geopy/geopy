
import unittest

from geopy.geocoders import GeoNames
from test.geocoders.util import GeocoderTestBase, CommonTestMixin, env

@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['GEONAMES_USERNAME'] is not None,
    "No GEONAMES_USERNAME env variable set"
)
class GeoNamesTestCase(GeocoderTestBase, CommonTestMixin):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = GeoNames(username=env['GEONAMES_USERNAME'])
        cls.delta = 0.04


