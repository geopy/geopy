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

from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT
from geopy.geocoders import *
from geopy.point import Point
from geopy.compat import py3k
from collections import defaultdict

if py3k:
    str_coerce = str
else:
    str_coerce = unicode

try:
    with open(".test_keys") as fp:
        env = defaultdict(lambda: None)
        env.update(json.loads(fp.read()))
except IOError:
    env = {
        'YAHOO_KEY': os.environ.get('YAHOO_KEY', None),
        'YAHOO_SECRET': os.environ.get('YAHOO_SECRET', None),
        'BING_KEY': os.environ.get('BING_KEY', None),
        'MAPQUEST_KEY': os.environ.get('MAPQUEST_KEY', None),
        'GEONAMES_USERNAME': os.environ.get('GEONAMES_USERNAME', None),
        'LIVESTREETS_AUTH_KEY': os.environ.get('LIVESTREETS_AUTH_KEY', None)
    }

# Define some generic test functions that are common to all backends


class LocalTestCase(unittest.TestCase):

    def test_init(self):
        """
        Geocoder()
        """
        format_string = '%s Los Angeles, CA USA'
        scheme = 'http'
        timeout = DEFAULT_TIMEOUT + 1
        proxies = {'https': '192.0.2.0'}
        geocoder = Geocoder(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies
        )
        for attr in ('format_string', 'scheme', 'timeout', 'proxies'):
            self.assertEqual(locals()[attr], getattr(geocoder, attr))

    def test_point_coercion(self):
        """
        Geocoder._coerce_point_to_string
        """
        ok = "40.74113,-73.989656"
        coords = (40.74113, -73.989656)
        geocoder = Geocoder()
        self.assertEqual(geocoder._coerce_point_to_string(coords), ok) # pylint: disable=W0212
        self.assertEqual(geocoder._coerce_point_to_string( # pylint: disable=W0212
            Point(*coords)),
            ok
        )

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
        self.skip_known_failure(('GeocoderDotUS', 'GeoNames', 'Nominatim'))

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
        self.skip_known_failure(('OpenMapQuest', 'GeoNames', 'LiveAddress', 'Nominatim'))

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
        self.geocoder = GoogleV3()

    def test_reverse(self):
        known_addr = '1060-1078 Avenue of the Americas, New York, NY 10018, USA'
        known_coords = (40.75376406311989, -73.98489005863667)
        addr, coords = self.geocoder.reverse(
            "40.75376406311989, -73.98489005863667",
            exactly_one=True
        )
        self.assertEqual(str_coerce(addr), known_addr)
        self.assertAlmostEqual(coords[0], known_coords[0], delta=self.delta_exact)
        self.assertAlmostEqual(coords[1], known_coords[1], delta=self.delta_exact)

    def test_zero_results(self):
        result = self.geocoder.geocode('')
        self.assertIsNone(result)


@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['BING_KEY'] is not None,
    "No BING_KEY env variable set"
)
class BingTestCase(_BackendTestCase):
    def setUp(self):
        self.geocoder = Bing(
            format_string='%s',
            api_key=env['BING_KEY']
        )

    def test_reverse(self):
        known_addr = '1067 6th Ave, New York, NY 10018, United States'
        known_coords = (40.75376406311989, -73.98489005863667)
        addr, coords = self.geocoder.reverse(Point(40.753898, -73.985071))
        self.assertEqual(str_coerce(addr), known_addr)
        self.assertAlmostEqual(coords[0], known_coords[0], delta=self.delta_exact)
        self.assertAlmostEqual(coords[1], known_coords[1], delta=self.delta_exact)

    def test_user_location(self):
        pensylvania = "20 Main St, Bally, PA 19503, United States"
        colorado = "20 Main St, Broomfield, CO 80020, United States"

        pennsylvania_bias = (40.922351, -75.096562)
        colorado_bias = (39.914231, -105.070104)
        for each in ((pensylvania, pennsylvania_bias), (colorado, colorado_bias)):
            self.assertEqual(
                self.geocoder.geocode(
                    "20 Main Street", user_location=Point(each[1])
                )[0],
                each[0]
            )

class GeocoderDotUSTestCase(_BackendTestCase): # pylint: disable=R0904,C0111
    def setUp(self):
        self.geocoder = GeocoderDotUS(timeout=3)


class OpenMapQuestTestCase(_BackendTestCase): # pylint: disable=R0904,C0111
    def setUp(self):
        self.geocoder = OpenMapQuest(timeout=3)
        self.delta_exact = 0.04
        self.delta_placename = 0.04


@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['MAPQUEST_KEY'] is not None,
    "No MAPQUEST_KEY env variable set"
)
class MapQuestTestCase(_BackendTestCase):
    def setUp(self):
        self.geocoder = MapQuest(env['MAPQUEST_KEY'], timeout=3)
        self.delta_placename = 0.04


@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['GEONAMES_USERNAME'] is not None,
    "No GEONAMES_USERNAME env variable set"
)
class GeoNamesTestCase(_BackendTestCase):
    def setUp(self):
        self.geocoder = GeoNames(username=env['GEONAMES_USERNAME'])
        self.delta_placename = 0.04


@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['LIVESTREETS_AUTH_KEY'] is not None,
    "No LIVESTREETS_AUTH_KEY env variable set"
)
class LiveAddressTestCase(_BackendTestCase):
    def setUp(self):
        self.geocoder = LiveAddress(
            auth_token=env['LIVESTREETS_AUTH_KEY']
        )
        self.delta_placename = 0.04


class NominatimTestCase(_BackendTestCase): # pylint: disable=R0904,C0111
    def setUp(self):
        self.geocoder = Nominatim()

    def test_reverse(self):
        known_addr = 'Jose Bonifacio de Andrada e Silva, 6th Avenue, Diamond '\
            'District, Manhattan, NYC, New York, 10020, United States of America'
        known_coords = (40.75376406311989, -73.98489005863667)
        addr, coords = self.geocoder.reverse(
            "40.75376406311989, -73.98489005863667",
            exactly_one=True
        )
        self.assertEqual(str_coerce(addr), known_addr)
        self.assertAlmostEqual(coords[0], known_coords[0], delta=self.delta_exact)
        self.assertAlmostEqual(coords[1], known_coords[1], delta=self.delta_exact)


@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['YAHOO_KEY'] is not None and env['YAHOO_SECRET'] is not None,
    "YAHOO_KEY and YAHOO_SECRET env variables not set"
)
class YahooPlaceFinderTestCase(_BackendTestCase): # pylint: disable=R0904,C0111
    def setUp(self):
        self.geocoder = YahooPlaceFinder()
