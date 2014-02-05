# encoding: utf-8
"""
Test Point.
"""

import unittest
from geopy.point import Point

class PointTestCase(unittest.TestCase): # pylint: disable=R0904
    """
    geopy.point.Point
    """

    lat = 40.74113
    lon = -73.989656
    alt = 3
    coords = (lat, lon, alt)

    def test_point_float(self):
        """
        Point() floats
        """
        point = Point(self.lat, self.lon, self.alt)
        self.assertEqual(point.longitude, self.lon)
        self.assertEqual(point.latitude, self.lat)
        self.assertEqual(point.altitude, self.alt)

    def test_point_str_simple(self):
        """
        Point() str
        """
        for each in ("%s,%s", "%s %s", "%s;%s"):
            point = Point(each % (self.lat, self.lon))
            self.assertEqual(point.longitude, self.lon)
            self.assertEqual(point.latitude, self.lat)

    def test_point_str_deg(self):
        """
        Point() str degrees, minutes &c
        """
        point = Point((u"UT: N 39°20' 0'' / W 74°35' 0''"))
        self.assertEqual(point.latitude, 39.333333333333336)
        self.assertEqual(point.longitude, -74.58333333333333)
        self.assertEqual(point.altitude, 0)

    def test_point_getitem(self):
        """
        Point.__getitem__
        """
        point = Point(self.lat, self.lon, self.alt)
        self.assertEqual(point[0], self.lat)
        self.assertEqual(point[1], self.lon)
        self.assertEqual(point[2], self.alt)

    def test_point_setitem(self):
        """
        Point.__setitem__
        """
        point = Point(self.lat + 10, self.lon + 10, self.alt + 10)
        for each in (0, 1, 2):
            point[each] = point[each] - 10
        self.assertEqual(point[0], self.lat)
        self.assertEqual(point[1], self.lon)
        self.assertEqual(point[2], self.alt)

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
            Point(self.lat, self.lon, self.alt) !=
            Point(self.lat+10, self.lon-10, self.alt)
        )



