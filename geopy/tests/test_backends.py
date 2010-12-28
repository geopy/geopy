import unittest

# Define some generic test functions that are common to all backends

def _basic_address_test(self):
    address = '999 W. Riverside Ave., Spokane, WA 99201'
    
    clean_address, latlon = self.geocoder.geocode(address)
    lat, lon = latlon
    
    self.failUnlessAlmostEqual(lat, 47.658, delta=.002)
    self.failUnlessAlmostEqual(lon, -117.426, delta=.002)
    
def _partial_address_test(self):
    address = '435 north michigan, chicago 60611'
    
    clean_address, latlon = self.geocoder.geocode(address)
    lat, lon = latlon
    
    self.failUnlessAlmostEqual(lat, 41.890, delta=.002)
    self.failUnlessAlmostEqual(lon, -87.624, delta=.002)

def _intersection_test(self):
    address = 'e. 161st st & river ave, new york, ny'
    
    clean_address, latlon = self.geocoder.geocode(address)
    lat, lon = latlon
    
    self.failUnlessAlmostEqual(lat, 40.828, delta=.002)
    self.failUnlessAlmostEqual(lon, -73.926, delta=.002)
    
# ==========
# Define the test cases that actually perform the import and instantiation step

class GoogleTestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.google import Google
        self.geocoder = Google()

class BingTestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.bing import Bing
        self.geocoder = Bing('Ao8kAepVCp_mQ583XgHg-rga2dwneQ4LtivmtuDj307vGjteiiqfI6ggjmx63wYR')

class YahooTestCase(unittest.TestCase):
    def setUp(self):
        from geopy.geocoders.yahoo import Yahoo
        self.geocoder = Yahoo('IhDhBmjV34Es_uagpOkitrTdVbd71SFfJptjhE_MTV9kOpjrQ.TFWU.33viYp5_k')

TESTCASES = [GoogleTestCase, BingTestCase, YahooTestCase]

# ==========
# Monkey patch the "generic" test functions into the testcases above

for x in TESTCASES:
    x.test_basic_address = _basic_address_test
    x.test_partial_address = _partial_address_test
    x.test_intersection = _intersection_test

# ==========

def get_suite():
    test_methods = [
        'test_basic_address',
        'test_partial_address',
        'test_intersection',
    ]
    tests = []
    for tc in TESTCASES:
        tests.extend(map(tc,test_methods))

    return unittest.TestSuite(tests)

if __name__ == '__main__':
    unittest.main()
