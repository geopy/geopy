
import unittest

from geopy.geocoders import YahooPlaceFinder
from test.geocoders.util import GeocoderTestBase, env

@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['YAHOO_KEY'] is not None and env['YAHOO_SECRET'] is not None,
    "YAHOO_KEY and YAHOO_SECRET env variables not set"
)
class YahooPlaceFinderTestCase(GeocoderTestBase): # pylint: disable=R0904,C0111

    @classmethod
    def setUpClass(cls):
        cls.geocoder = YahooPlaceFinder(
            env['YAHOO_KEY'],
            env['YAHOO_SECRET']
        )

    def test_geocode(self):
        """
        YahooPlaceFinder.geocode
        """
        self.geocode_run(
            {"query": u"435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        """
        YahooPlaceFinder.geocode unicode
        """
        self.geocode_run(
            {"query": u"\u6545\u5bab"},
            {"latitude": 39.916, "longitude": 116.390},
        )
