
import unittest

from geopy.geocoders import YahooPlaceFinder
from test.geocoders.util import GeocoderTestBase, CommonTestMixin, env

@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['YAHOO_KEY'] is not None and env['YAHOO_SECRET'] is not None,
    "YAHOO_KEY and YAHOO_SECRET env variables not set"
)
class YahooPlaceFinderTestCase(GeocoderTestBase, CommonTestMixin): # pylint: disable=R0904,C0111

    @classmethod
    def setUpClass(cls):
        cls.geocoder = YahooPlaceFinder(
            env['YAHOO_KEY'],
            env['YAHOO_SECRET']
        )
