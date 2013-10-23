"""
Full tests of geocoders including HTTP access.
"""
import os
import unittest
from urllib2 import URLError

import socket
socket.setdefaulttimeout(3.0)

env = {
    'BING_KEY': os.environ.get('BING_KEY', None),
    'MAPQUEST_KEY': os.environ.get('MAPQUEST_KEY', 'Dmjtd%7Clu612007nq%2C20%3Do5-50zah'),
    'GEONAMES_USERNAME': os.environ.get('GEONAMES_USERNAME', None),
    'LIVESTREETS_AUTH_ID': os.environ.get('LIVESTREETS_AUTH_ID', None),
    'LIVESTREETS_AUTH_KEY': os.environ.get('LIVESTREETS_AUTH_KEY', None)
}

# Define some generic test functions that are common to all backends

def _basic_address_test(self):
    address = '999 W. Riverside Ave., Spokane, WA 99201'

    try:
        clean_address, latlon = self.geocoder.geocode(address)
    except TypeError as err:
        self.fail('No result found')
    except URLError as err:
        if "timed out" in str(err).lower():
            raise unittest.SkipTest('Geocoder service timed out')
        else:
            raise

    self.assertAlmostEqual(latlon[0], 47.658, delta=.002)
    self.assertAlmostEqual(latlon[1], -117.426, delta=.002)

def _partial_address_test(self):
    address = '435 north michigan, chicago 60611'

    try:
        clean_address, latlon = self.geocoder.geocode(address)
    except TypeError as err:
        self.fail('No result found')
    except URLError as err:
        if "timed out" in str(err).lower():
            raise unittest.SkipTest('Geocoder service timed out')
        else:
            raise

    self.assertAlmostEqual(latlon[0], 41.890, delta=.002)
    self.assertAlmostEqual(latlon[1], -87.624, delta=.002)

def _intersection_test(self):
    address = 'e. 161st st & river ave, new york, ny'

    try:
        clean_address, latlon = self.geocoder.geocode(address)
    except TypeError as err:
        self.fail('No result found')
    except URLError as err:
        if "timed out" in str(err).lower():
            raise unittest.SkipTest('Geocoder service timed out')
        else:
            raise

    self.assertAlmostEqual(latlon[0], 40.828, delta=.002)
    self.assertAlmostEqual(latlon[1], -73.926, delta=.002)

def _placename_test(self):
    address = 'Mount St. Helens'

    try:
        # Since a place name search is significantly less accurate,
        # allow multiple results to come in. We'll check the top one.
        clean_address, latlon = self.geocoder.geocode(address, exactly_one=False)[0]
    except TypeError as err:
        self.fail('No result found')
    except URLError as err:
        if "timed out" in str(err).lower():
            raise unittest.SkipTest('Geocoder service timed out')
        else:
            raise

    # And since this is a pretty fuzzy search, we'll only test to .02
    self.assertAlmostEqual(latlon[0], 46.1912, delta=.02)
    self.assertAlmostEqual(latlon[1], -122.1944, delta=.02)

# ==========
# Define the test cases that actually perform the import and instantiation step

class GoogleV3TestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.googlev3 import GoogleV3
        self.geocoder = GoogleV3()

@unittest.skipUnless(
    env['BING_KEY'] is not None,
    "No BING_KEY env variable set"
)
class BingTestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.bing import Bing
        self.geocoder = Bing(api_key=env['BING_KEY'])


class DotUSTestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.dot_us import GeocoderDotUS
        self.geocoder = GeocoderDotUS()


class OpenMapQuestTestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.openmapquest import OpenMapQuest
        self.geocoder = OpenMapQuest()

    # Does not do fuzzy address search.
    test_basic_address = _basic_address_test
    test_placename = _placename_test


@unittest.skipUnless(
    env['MAPQUEST_KEY'] is not None,
    "No MAPQUEST_KEY env variable set"
)
class MapQuestTestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.mapquest import MapQuest
        self.geocoder = MapQuest(env['MAPQUEST_KEY'])

    # Does not do fuzzy address search.
    test_basic_address = _basic_address_test
    test_placename = _placename_test

@unittest.skipUnless(
    env['GEONAMES_USERNAME'] is not None,
    "No GEONAMES_USERNAME env variable set"
)
class GeoNamesTestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.geonames import GeoNames
        self.geocoder = GeoNames(username=env['GEONAMES_USERNAME'])

    # Does not do any address searching.
    test_placename = _placename_test

@unittest.skipUnless(
    env['LIVESTREETS_AUTH_ID'] is not None and \
    env['LIVESTREETS_AUTH_KEY'] is not None,
    "LIVESTREETS_AUTH_ID and LIVESTREETS_AUTH_KEY env variables not set"
)
class LiveAddressTestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.smartystreets import LiveAddress
        self.geocoder = LiveAddress(
            auth_id=env['LIVESTREETS_AUTH_ID'],
            auth_token=env['LIVESTREETS_AUTH_KEY']
        )

    # Does not do any placename or intersection searching.
    test_basic_address = _basic_address_test
    test_partial_address = _partial_address_test


BASIC_TESTCASES = [
    GoogleV3TestCase,
    BingTestCase,
    DotUSTestCase,
    MapQuestTestCase,
    LiveAddressTestCase
]


# ==========
# Monkey patch the "generic" test functions into the testcases above

for x in BASIC_TESTCASES:
    x.test_basic_address = _basic_address_test
    x.test_partial_address = _partial_address_test
    x.test_intersection = _intersection_test
    x.test_placename = _placename_test

# ==========

def get_suite():
    test_methods = [
        'test_basic_address',
        'test_partial_address',
        'test_intersection',
        'test_placename',
    ]
    tests = []
    for tc in BASIC_TESTCASES:
        tests.extend(map(tc,test_methods))

    tests.append(OpenMapQuestTestCase('test_basic_address'))
    tests.append(OpenMapQuestTestCase('test_placename'))
    tests.append(MapQuestTestCase('test_basic_address'))
    tests.append(MapQuestTestCase('test_placename'))
    tests.append(GeoNamesTestCase('test_placename'))
    tests.append(LiveAddressTestCase('test_basic_address'))
    tests.append(LiveAddressTestCase('test_partial_address'))

    return unittest.TestSuite(tests)

if __name__ == '__main__':
    unittest.main()
