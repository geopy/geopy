import unittest
from urllib2 import URLError

import socket
socket.setdefaulttimeout(3.0)

# Define some generic test functions that are common to all backends

def _basic_address_test(self):
    address = '999 W. Riverside Ave., Spokane, WA 99201'
    
    try:
        clean_address, latlon = self.geocoder.geocode(address)
    except URLError as e:
        if "timed out" in str(e).lower():
            raise unittest.SkipTest('geocoder service timed out')
        else:
            raise
    
    self.assertAlmostEqual(latlon[0], 47.658, delta=.002)
    self.assertAlmostEqual(latlon[1], -117.426, delta=.002)
    
def _partial_address_test(self):
    address = '435 north michigan, chicago 60611'
    
    try:
        clean_address, latlon = self.geocoder.geocode(address)
    except URLError as e:
        if "timed out" in str(e).lower():
            raise unittest.SkipTest('geocoder service timed out')
        else:
            raise
    
    self.assertAlmostEqual(latlon[0], 41.890, delta=.002)
    self.assertAlmostEqual(latlon[1], -87.624, delta=.002)

def _intersection_test(self):
    address = 'e. 161st st & river ave, new york, ny'
    
    try:
        clean_address, latlon = self.geocoder.geocode(address)
    except URLError as e:
        if "timed out" in str(e).lower():
            raise unittest.SkipTest('geocoder service timed out')
        else:
            raise
    
    self.assertAlmostEqual(latlon[0], 40.828, delta=.002)
    self.assertAlmostEqual(latlon[1], -73.926, delta=.002)

def _placename_test(self):
    address = 'Mount St. Helens'
    
    try:
        # Since a place name search is significantly less accurate,
        # allow multiple results to come in. We'll check the top one.
        places = self.geocoder.geocode(address, exactly_one=False)
    except URLError as e:
        if "timed out" in str(e).lower():
            raise unittest.SkipTest('geocoder service timed out')
        else:
            raise
    
    place = places[0]
    clean_address, latlon = place
    
    # And since this is a pretty fuzzy search, we'll only test to .02
    self.assertAlmostEqual(latlon[0], 46.1912, delta=.02)
    self.assertAlmostEqual(latlon[1], -122.1944, delta=.02)
    
# ==========
# Define the test cases that actually perform the import and instantiation step

class GoogleTestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.google import Google
        self.geocoder = Google()

class GoogleV3TestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.googlev3 import GoogleV3
        self.geocoder = GoogleV3()

class BingTestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.bing import Bing
        self.geocoder = Bing('Ao8kAepVCp_mQ583XgHg-rga2dwneQ4LtivmtuDj307vGjteiiqfI6ggjmx63wYR')

class YahooTestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.yahoo import Yahoo
        self.geocoder = Yahoo('IhDhBmjV34Es_uagpOkitrTdVbd71SFfJptjhE_MTV9kOpjrQ.TFWU.33viYp5_k')

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

class MapQuestTestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.mapquest import MapQuest
        self.geocoder = MapQuest('Dmjtd%7Clu612007nq%2C20%3Do5-50zah')
    
    # Does not do fuzzy address search.
    test_basic_address = _basic_address_test
    test_placename = _placename_test

class GeoNamesTestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.geonames import GeoNames
        self.geocoder = GeoNames()
    
    # Does not do any address searching.
    test_placename = _placename_test

BASIC_TESTCASES = [GoogleTestCase, GoogleV3TestCase, BingTestCase, DotUSTestCase, YahooTestCase]

# geonames does not actually test against addresses (just place names)
#TESTCASES = [GoogleTestCase, BingTestCase, YahooTestCase, DotUSTestCase, GeoNamesTestCase]


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
    
    return unittest.TestSuite(tests)

if __name__ == '__main__':
    unittest.main()
