#!/usr/bin/env python
import unittest, os, logging
from geopy import Point
from geopy.parsers import gpx

from datetime import datetime
from geopy.parsers.iso8601 import TimeZone

log = logging.getLogger('geopy.parsers.gpx')

TEST_FILE = os.path.join(
              os.path.dirname(__file__), 'fells_loop.gpx')
            # From http://www.topografix.com/fells_loop.gpx

class GPX(object):
    def test_version(self):
        self.assertTrue(self.GPXi.version == '1.1')

    def test_creator(self):
        self.assertTrue(
          self.GPXi.creator == 'ExpertGPS 1.1 - http://www.topografix.com')

    def test_route_names(self):
        names = list(self.GPXi.route_names)
        self.assertTrue(names == ['BELLEVUE (first three waypoints)',
                                  'BELLEVUE'])

    def test_route_list(self):
        route = list(self.GPXi.get_waypoints(
            'BELLEVUE (first three waypoints)'))
        self.assertTrue(route == [Point(42.430950, -71.107628, 23.469600),
                                  Point(42.431240, -71.109236, 26.561890),
                                  Point(42.434980, -71.109942, 45.307495)])
        second_top_level_waypoint = list(self.GPXi.waypoints)[1]
        self.assertTrue(second_top_level_waypoint ==
                          Point(42.439227, -71.119689, 57.607200))
        self.assertTrue(second_top_level_waypoint.timestamp ==
          datetime(2001, 6, 2, 3, 26, 55, tzinfo = TimeZone('UTC')))
        self.assertTrue(second_top_level_waypoint.name == '5067')
        self.assertTrue(second_top_level_waypoint.description == '5067')

class GPXInitTestCase(GPX, unittest.TestCase):
    """ Tests GPX parser, when the parser is instantiated with a file object """
    def setUp(self):
        self.f = open(TEST_FILE, 'r')
        self.GPXi = gpx.GPX(self.f)

    def tearDown(self):
        self.f.close()

class GPXOpenerTestCase(GPX, unittest.TestCase):
    """ Tests GPX parser, when file is loaded via the .open() method """
    def setUp(self):
        self.f = open(TEST_FILE, 'r')
        self.GPXi = gpx.GPX()
        self.GPXi.open(self.f)

    def tearDown(self):
        self.f.close()

def get_suite():
    test_methods = [
        'test_version',
        'test_creator',
        'test_route_names',
        'test_route_list',
    ]
    tests = []
    tests.extend(map(GPXInitTestCase,test_methods))
    tests.extend(map(GPXOpenerTestCase,test_methods))

    return unittest.TestSuite(tests)

if __name__ == '__main__':
    unittest.main()
