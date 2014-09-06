
import unittest

from geopy.point import Point
from geopy.geocoders import YahooPlaceFinder
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(  # pylint: disable=R0904,C0111
    bool(env.get('YAHOO_KEY')) and bool(env.get('YAHOO_SECRET')),
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
            {"query": u"nyc"},
            {"latitude": 40.71455, "longitude": -74.00712},
        )

    def test_unicode_name(self):
        """
        YahooPlaceFinder.geocode unicode
        """
        self.geocode_run(
            {"query": u"\u6545\u5bab"},
            {"latitude": 39.916, "longitude": 116.390},
        )

    def test_reverse_string(self):
        """
        YahooPlaceFinder.reverse string
        """
        self.reverse_run(
            {"query": u"40.75376406311989, -73.98489005863667"},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667}
        )

    def test_reverse_point(self):
        """
        YahooPlaceFinder.reverse Point
        """
        self.reverse_run(
            {"query": Point(40.75376406311989, -73.98489005863667)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667}
        )
