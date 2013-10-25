"""
Full tests of geocoders including HTTP access.
"""
import os
import unittest

import json

try:
    from urllib2 import URLError
except ImportError:
    from urllib.error import URLError # pylint: disable=F0401,E0611

import socket
socket.setdefaulttimeout(3.0)

from geopy.point import Point

try:
    with open(".test_keys") as fp:
        env = json.loads(fp.read())
except IOError:
    env = {
        'BING_KEY': os.environ.get('BING_KEY', None),
        'MAPQUEST_KEY': os.environ.get('MAPQUEST_KEY', None),
        'GEONAMES_USERNAME': os.environ.get('GEONAMES_USERNAME', None),
        'LIVESTREETS_AUTH_KEY': os.environ.get('LIVESTREETS_AUTH_KEY', None)
    }

# Define some generic test functions that are common to all backends



class _BackendTestCase(unittest.TestCase): # pylint: disable=R0904
    """
    Base for geocoder-specific test cases.
    """

    geocoder = None
    delta_exact = 0.002
    delta_placename = 0.02

    def skip_known_failure(self, classes):
        """
        When a Geocoder gives no value for a query, skip the test.
        """
        if self.geocoder.__class__.__name__ in classes:
            raise unittest.SkipTest("%s is known to not have results for this query" % \
                self.geocoder.__class__.__name__
            )

    def test_basic_address(self):
        self.skip_known_failure(('GeocoderDotUS', 'GeoNames', ))

        address = '999 W. Riverside Ave., Spokane, WA 99201'

        try:
            result = self.geocoder.geocode(address)
        except URLError as err:
            if "timed out" in str(err).lower():
                raise unittest.SkipTest('Geocoder service timed out')
            else:
                raise
        if result is None:
            self.fail('No result found')
        clean_address, latlon = result # pylint: disable=W0612

        self.assertAlmostEqual(latlon[0], 47.658, delta=self.delta_exact)
        self.assertAlmostEqual(latlon[1], -117.426, delta=self.delta_exact)

    def test_partial_address(self):
        self.skip_known_failure(('GeocoderDotUS', 'GeoNames', ))

        address = '435 north michigan, chicago 60611'

        try:
            result = self.geocoder.geocode(address)

        except URLError as err:
            if "timed out" in str(err).lower():
                raise unittest.SkipTest('Geocoder service timed out')
            else:
                raise
        if result is None:
            self.fail('No result found')
        clean_address, latlon = result # pylint: disable=W0612

        self.assertAlmostEqual(latlon[0], 41.890, delta=self.delta_exact)
        self.assertAlmostEqual(latlon[1], -87.624, delta=self.delta_exact)

    def test_intersection(self):
        self.skip_known_failure(('OpenMapQuest', 'GeoNames', 'LiveAddress'))

        address = 'e. 161st st & river ave, new york, ny'

        try:
            result = self.geocoder.geocode(address, exactly_one=True)
        except URLError as err:
            if "timed out" in str(err).lower():
                raise unittest.SkipTest('Geocoder service timed out')
            else:
                raise
        if result is None:
            self.fail('No result found')
        clean_address, latlon = result # pylint: disable=W0612

        self.assertAlmostEqual(latlon[0], 40.828, delta=self.delta_exact)
        self.assertAlmostEqual(latlon[1], -73.926, delta=self.delta_exact)

    def test_placename(self):
        self.skip_known_failure(('GeocoderDotUS', 'LiveAddress'))

        address = 'Mount St. Helens'

        try:
            # Since a place name search is significantly less accurate,
            # allow multiple results to come in. We'll check the top one.
            result = self.geocoder.geocode(address, exactly_one=False)
        except URLError as err:
            if "timed out" in str(err).lower():
                raise unittest.SkipTest('Geocoder service timed out')
            else:
                raise
        if result is None or not len(result):
            self.fail('No result found')
        clean_address, latlon = result[0] # pylint: disable=W0612

        # And since this is a pretty fuzzy search, we'll only test to .02
        self.assertAlmostEqual(latlon[0], 46.1912, delta=self.delta_placename)
        self.assertAlmostEqual(latlon[1], -122.1944, delta=self.delta_placename)



class GoogleV3TestCase(_BackendTestCase): # pylint: disable=R0904,C0111
    def setUp(self):
        from geopy.geocoders.googlev3 import GoogleV3
        self.geocoder = GoogleV3()

    def test_reverse(self):
        known_addr = '1060-1078 Avenue of the Americas, New York, NY 10018, USA'
        known_coords = (40.75376406311989, -73.98489005863667)
        addr, coords = self.geocoder.reverse(
            "40.75376406311989, -73.98489005863667",
            exactly_one=True
        )
        self.assertEqual(str(addr), known_addr)
        self.assertAlmostEqual(coords[0], known_coords[0], delta=self.delta_exact)
        self.assertAlmostEqual(coords[1], known_coords[1], delta=self.delta_exact)


@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['BING_KEY'] is not None,
    "No BING_KEY env variable set"
)
class BingTestCase(_BackendTestCase):
    def setUp(self):
        from geopy.geocoders.bing import Bing
        self.geocoder = Bing(
            format_string='%s',
            api_key=env['BING_KEY']
        )

    def test_reverse(self):
        known_addr = '1067 6th Ave, New York, NY 10018, United States'
        known_coords = (40.75376406311989, -73.98489005863667)
        addr, coords = self.geocoder.reverse(Point(40.753898, -73.985071))
        self.assertEqual(str(addr), known_addr)
        self.assertAlmostEqual(coords[0], known_coords[0], delta=self.delta_exact)
        self.assertAlmostEqual(coords[1], known_coords[1], delta=self.delta_exact)


class GeocoderDotUSTestCase(_BackendTestCase): # pylint: disable=R0904,C0111
    def setUp(self):
        from geopy.geocoders.dot_us import GeocoderDotUS
        self.geocoder = GeocoderDotUS()


class OpenMapQuestTestCase(_BackendTestCase): # pylint: disable=R0904,C0111
    def setUp(self):
        from geopy.geocoders.openmapquest import OpenMapQuest
        self.geocoder = OpenMapQuest()
        self.delta_exact = 0.04
        self.delta_placename = 0.04


@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['MAPQUEST_KEY'] is not None,
    "No MAPQUEST_KEY env variable set"
)
class MapQuestTestCase(_BackendTestCase):
    def setUp(self):
        from geopy.geocoders.mapquest import MapQuest
        self.geocoder = MapQuest(env['MAPQUEST_KEY'])
        self.delta_placename = 0.04

@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['GEONAMES_USERNAME'] is not None,
    "No GEONAMES_USERNAME env variable set"
)
class GeoNamesTestCase(_BackendTestCase):
    def setUp(self):
        from geopy.geocoders.geonames import GeoNames
        self.geocoder = GeoNames(username=env['GEONAMES_USERNAME'])
        self.delta_placename = 0.04

@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['LIVESTREETS_AUTH_KEY'] is not None,
    "LIVESTREETS_AUTH_ID and LIVESTREETS_AUTH_KEY env variables not set"
)
class LiveAddressTestCase(_BackendTestCase):
    def setUp(self):
        from geopy.geocoders.smartystreets import LiveAddress
        self.geocoder = LiveAddress(
            auth_token=env['LIVESTREETS_AUTH_KEY']
        )
        self.delta_placename = 0.04

# class YahooPlaceFinderTestCase(_BackendTestCase): # pylint: disable=R0904,C0111
#     def setUp(self):
#         from geopy.geocoders.placefinder import YahooPlaceFinder
#         self.geocoder = YahooPlaceFinder()
