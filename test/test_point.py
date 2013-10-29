"""
Test Point.
"""

import unittest
from geopy.point import Point

class PointTestCase(unittest.TestCase): # pylint: disable=R0904

    lat = 40.74113
    lon = -73.989656
    alt = 3
    coords = (lat, lon, alt)

    def test_point_ok_float(self):
        """
        Point() floats
        """
        point = Point(self.lat, self.lon, self.alt)
        self.assertEqual(point.longitude, self.lon)
        self.assertEqual(point.latitude, self.lat)
        self.assertEqual(point.altitude, self.alt)

    def test_point_ok_str(self):
        """
        Point() str
        """
        point = Point("%s %s" % (self.lat, self.lon))
        self.assertEqual(point.longitude, self.lon)
        self.assertEqual(point.latitude, self.lat)

    def test_point_eq(self):
        """
        Point.__eq__
        """
        self.assertEqual(
            Point(self.lat, self.lon),
            Point("%s %s" % (self.lat, self.lon))
        )

    def test_point_ne(self):
        """
        Point.__ne__
        """
        self.assertTrue(
            Point(self.lat, self.lon, self.alt) != Point(self.lat+10, self.lon-10, self.alt)
        )



