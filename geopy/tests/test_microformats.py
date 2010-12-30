#!/usr/bin/env python
import unittest
from geopy import format, Location, Point
from geopy.parsers.html import GeoMicroformat
from BeautifulSoup import BeautifulSoup

class GeoMicroformatFound(object):
    def setUp(self):
        self.parser = GeoMicroformat()
    
    def test_one_str(self):
        locations = self.parser.find_all(self.MARKUP)
        self.assertTrue(len(locations) == 1)
        self._location_test(locations[0])

    def test_multi_str(self):
        locations = self.parser.find_all(self.MARKUP * 3)
        self.assertTrue(len(locations) == 3)
        for i in range(3):
            self._location_test(locations[i])

    def test_one_soup(self):
        if BeautifulSoup:
            locations = self.parser.find_all(BeautifulSoup(self.MARKUP))
            self.assertTrue(len(locations) == 1)
            self._location_test(locations[0])

    def test_multi_soup(self):
        if BeautifulSoup:
            locations = self.parser.find_all(BeautifulSoup(self.MARKUP * 3))
            self.assertTrue(len(locations) == 3)
            for i in range(3):
                self._location_test(locations[i])

    def _location_test(self, location):
        self.assertTrue(location.name == self.NAME)
        self.assertTrue(location.point == self.POINT)

class GeoMicroformatNotFound(object):
    def setUp(self):
        self.parser = GeoMicroformat()
    
    def test_none_str(self):
        locations = self.parser.find_all(self.MARKUP)
        self.assertTrue(len(locations) == 0)
    
    def test_none_soup(self):
        if BeautifulSoup:
            locations = self.parser.find_all(BeautifulSoup(self.MARKUP))
            self.assertTrue(len(locations) == 0)

class GeoMicroformatFoundTest(GeoMicroformatFound, unittest.TestCase):
    MARKUP = """
    <span class="geo">
      <span class="latitude">41.4924</span>;
      <span class="longitude">-81.7239</span>
    </span>
    """
    NAME = "41.4924; -81.7239"
    POINT = Point(41.4924, -81.7239)

class GeoMicroformatNotFoundTest(GeoMicroformatNotFound, unittest.TestCase):
    MARKUP = """
    <span>
      <span class="latitude">41.4924</span>;
      <span class="longitude">-81.7239</span>
    </span>
    """

class FindAbbrLatLongTest(GeoMicroformatFoundTest):
    MARKUP = """
    <span class="geo">
        <abbr class="latitude" title="41.4924">N 41.5</abbr>,
        <abbr class="longitude" title="-81.7239">W 81.7</abbr>
    </span>
    """
    NAME = "N 41.5, W 81.7"

class FindAbbrShorthandTest(GeoMicroformatFoundTest):
    MARKUP = """
    <abbr class="geo" title="41.4924;-81.7239">N 41.5, W 81.7</abbr>
    """
    NAME = "N 41.5, W 81.7"

class NoShorthandNotFoundTest(GeoMicroformatNotFoundTest):
    def setUp(self):
        self.parser = GeoMicroformat(shorthand=False)
    
    MARKUP = """<span class="geo">41.4924;-81.7239</span>"""

class NoShorthandFoundTest(GeoMicroformatFoundTest):
    def setUp(self):
        self.parser = GeoMicroformat(shorthand=False)
    
    MARKUP = """
    <span class="geo">41.4924;-81.7239</span>
    <span class="geo">
      <span class="latitude">41.4924</span>;
      <span class="longitude">-81.7239</span>
    </span>
    <abbr class="geo" title="41.4924;-81.7239">N 41.5, W 81.7</abbr>
    """

class FindNestedDefListTest(GeoMicroformatFoundTest):
    MARKUP = """
    <dl>
      <dt>Geo</dt>
      <dd class="geo">
        <dl>
          <dt>Latitude</dt>
          <dd><abbr class="latitude" title="12.3456789">12&deg;20' 44" N</abbr></dd>
          <dt>Longitude</dt>
          <dd><abbr class="longitude" title="-123.456789">123&deg;27' 24" W</abbr></dd>
        </dl>
      </dd>
    </dl>
    """
    NAME = "Latitude 12%s20' 44\" N" \
           " Longitude 123%s27' 24\" W" % (format.DEGREE, format.DEGREE)
    POINT = Point(12.3456789, -123.456789)

def get_suite():
    """
    Returns a TestSuite containing all of the TestCases for microformats. If BeautifulSoup
    isn't installed, then tests against that library are skipped.
    """
    
    geofound_test_methods = [
        'test_one_str',
        'test_multi_str',
    ]
    geonotfound_test_methods = [
        'test_none_str',
    ]
    if BeautifulSoup:
        geofound_test_methods.extend(['test_one_soup','test_multi_soup',])
        geonotfound_test_methods.append('test_none_soup')
    
    tests = []
    tests.extend(map(GeoMicroformatFoundTest,geofound_test_methods))
    tests.extend(map(FindAbbrLatLongTest,geofound_test_methods))
    tests.extend(map(FindAbbrShorthandTest,geofound_test_methods))
    tests.extend(map(NoShorthandFoundTest,geofound_test_methods))
    tests.extend(map(FindNestedDefListTest,geofound_test_methods))
    
    tests.extend(map(GeoMicroformatNotFoundTest,geonotfound_test_methods))
    tests.extend(map(NoShorthandNotFoundTest,geonotfound_test_methods))
    
    return unittest.TestSuite(tests)

if __name__ == '__main__':
    unittest.main()
