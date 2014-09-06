
import unittest

from geopy.point import Point
from geopy.geocoders import Bing
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(  # pylint: disable=R0904,C0111
    bool(env.get('BING_KEY')),
    "No BING_KEY env variable set"
)
class BingTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Bing(
            format_string='%s',
            scheme='http',
            api_key=env['BING_KEY']
        )

    def test_geocode(self):
        """
        Bing.geocode
        """
        self.geocode_run(
            {"query": u"435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        """
        Bing.geocode unicode
        """
        self.geocode_run(
            {"query": u"\u6545\u5bab"},
            {"latitude": 39.916, "longitude": 116.390},
        )

    def test_reverse_point(self):
        """
        Bing.reverse using point
        """
        self.reverse_run(
            {"query": Point(40.753898, -73.985071)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    def test_user_location(self):
        """
        Bing.geocode using `user_location`
        """
        pensylvania = "20 Main St, Bally, PA 19503, United States"
        colorado = "20 Main St, Broomfield, CO 80020, United States"

        pennsylvania_bias = (40.922351, -75.096562)
        colorado_bias = (39.914231, -105.070104)
        for each in (
                (pensylvania, pennsylvania_bias),
                (colorado, colorado_bias)
            ):
            self.assertEqual(
                self.geocoder.geocode(
                    "20 Main Street", user_location=Point(each[1])
                )[0],
                each[0]
            )
