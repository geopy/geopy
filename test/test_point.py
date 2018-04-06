"""
Test Point.
"""

import pickle
import unittest
import math

from geopy.compat import u
from geopy.point import Point


class PointTestCase(unittest.TestCase):
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
            self.assertEqual(point.altitude, 0)

    def test_point_str_deg(self):
        """
        Point() str degrees, minutes &c
        """
        point = Point(u("UT: N 39\xb020' 0'' / W 74\xb035' 0''"))
        self.assertEqual(point.latitude, 39.333333333333336)
        self.assertEqual(point.longitude, -74.58333333333333)
        self.assertEqual(point.altitude, 0)

    def test_point_format(self):
        """
        Point.format()
        """
        point = Point("51 19m 12.9s N, 0 1m 24.95s E")
        self.assertEqual(point.format(), "51 19m 12.9s N, 0 1m 24.95s E")

        point = Point("51 19m 12.9s N, -1 1m 24.95s E, 15000m")
        self.assertEqual(point.format(), "51 19m 12.9s N, 1 1m 24.95s W, 15.0km")

        # TODO
        # point = Point("51 19m 12.9s N, -0 1m 24.95s E")
        # self.assertEqual(point.format(), "51 19m 12.9s N, 0 1m 24.95s W")

        # TODO
        # with self.assertRaises(ValueError):
        #     # Z is not a valid direction
        #     Point("51 19m 12.9s Z, 0 1m 24.95s E")

        with self.assertRaises(ValueError):
            Point("gibberish")

    def test_point_format_altitude(self):
        """
        Point.format() includes altitude
        """
        point = Point(latitude=41.5, longitude=81.0, altitude=2.5)
        self.assertEqual(point.format(), "41 30m 0s N, 81 0m 0s E, 2.5km")
        self.assertEqual(point.format_decimal(), "41.5, 81.0, 2.5km")
        self.assertEqual(point.format_decimal('m'), "41.5, 81.0, 2500.0m")

        point = Point(latitude=41.5, longitude=81.0)
        self.assertEqual(point.format_decimal(), "41.5, 81.0")
        self.assertEqual(point.format_decimal('m'), "41.5, 81.0, 0.0m")

    def test_point_from_iterable(self):
        self.assertEqual(Point(1, 2, 3), Point([1, 2, 3]))
        self.assertEqual(Point(1, 2, 0), Point([1, 2]))
        self.assertEqual(Point(1, 0, 0), Point([1]))
        self.assertEqual(Point(0, 0, 0), Point([]))

        with self.assertRaises(ValueError):
            Point([1, 2, 3, 4])

    def test_point_from_point(self):
        point = Point(self.lat, self.lon, self.alt)
        point_copy = Point(point)
        self.assertTrue(point is not point_copy)
        self.assertEqual(tuple(point), tuple(point_copy))

    def test_point_from_generator(self):
        point = Point(i + 10 for i in range(3))
        self.assertEqual((10, 11, 12), tuple(point))
        self.assertEqual((10, 11, 12), tuple(point))

    def test_point_degrees_are_normalized(self):
        point = Point(95, 185, 375)
        self.assertEqual((-85, -175, 375), tuple(point))
        point = Point(-95, -185, 375)
        self.assertEqual((85, 175, 375), tuple(point))
        point = Point(-0.0, -0.0, 375)
        self.assertEqual((0.0, 0.0, 375.0), tuple(point))  # note that the zeros might be negative
        # ensure that negative zeros are normalized to the positive ones
        self.assertEqual((1.0, 1.0, 1.0), tuple(math.copysign(1.0, x) for x in point))
        point = Point(90, 180, 375)
        self.assertEqual((90, 180, 375), tuple(point))
        point = Point(-90, -180, 375)
        self.assertEqual((-90, -180, 375), tuple(point))
        point = Point(-270, -540, 375)
        self.assertEqual((-90, -180, 375), tuple(point))
        point = Point(270, 540, 375)
        self.assertEqual((-90, -180, 375), tuple(point))

    def test_unpacking(self):
        point = Point(self.lat, self.lon, self.alt)
        lat, lon, alt = point
        self.assertEqual(lat, self.lat)
        self.assertEqual(lon, self.lon)
        self.assertEqual(alt, self.alt)

    def test_point_no_len(self):
        point = Point(self.lat, self.lon)  # is it 2 or 3?
        with self.assertRaises(TypeError):  # point doesn't support len()
            len(point)

    def test_point_getitem(self):
        """
        Point.__getitem__
        """
        point = Point(self.lat, self.lon, self.alt)
        self.assertEqual(point[0], self.lat)
        self.assertEqual(point[1], self.lon)
        self.assertEqual(point[2], self.alt)

    def test_point_slices(self):
        point = Point(self.lat, self.lon, self.alt)
        self.assertEqual((self.lat, self.lon), point[:2])

        self.assertEqual(self.coords, point[:10])
        self.assertEqual(self.coords, point[:])
        self.assertEqual(self.coords[::-1], point[::-1])

        with self.assertRaises(IndexError):
            point[10]

        with self.assertRaises(TypeError):
            point[None]

        point[0:2] = (self.lat + 10, self.lon + 10)
        self.assertEqual((self.lat + 10, self.lon + 10, self.alt),
                         tuple(point))

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

        self.assertEqual(self.coords, tuple(point))
        self.assertEqual(point.latitude, self.lat)
        self.assertEqual(point.longitude, self.lon)
        self.assertEqual(point.altitude, self.alt)

    def test_point_assign_coordinates(self):
        point = Point(self.lat + 10, self.lon + 10, self.alt + 10)
        point.latitude = self.lat
        point.longitude = self.lon
        point.altitude = self.alt

        self.assertEqual(point[0], self.lat)
        self.assertEqual(point[1], self.lon)
        self.assertEqual(point[2], self.alt)

        self.assertEqual(self.coords, tuple(point))
        self.assertEqual(point.latitude, self.lat)
        self.assertEqual(point.longitude, self.lon)
        self.assertEqual(point.altitude, self.alt)

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

    def test_point_comparison_does_not_raise_exceptions(self):
        point = Point(self.lat, self.lon, self.alt)
        number = 1
        not_iterable = object()
        self.assertFalse(point == number)
        self.assertTrue(point != number)
        self.assertFalse(point == not_iterable)
        self.assertTrue(point != not_iterable)

    def test_point_comparison_with_empty_values(self):
        empty_values = (None, '', [], (), {})  # Django validators
        point_nonempty = Point(self.lat, self.lon, self.alt)
        point_empty = Point()  # actually Point(0, 0, 0), which is not "empty"
        self.assertFalse(point_nonempty in empty_values)
        self.assertTrue(point_nonempty)

        # Point() == (0, 0, 0).
        self.assertEqual(Point(), (0, 0, 0))
        # Currently Point can't distinguish between zero and unset coordinate
        # values, so we cannot tell if `point_empty` is really "empty"
        # (i.e. unset, like `Point()`) or is just a point at the center
        # (which is obviously not "empty"). That's why on the next line
        # we assume that `point_empty` is not in the `empty_values` list.
        self.assertFalse(point_empty in empty_values)
        # bool(Point(0, 0, 0)) should also be true
        self.assertTrue(point_empty)

    def test_point_comparison_respects_lists(self):
        point = Point(self.lat, self.lon, self.alt)
        l_eq = [self.lat, self.lon, self.alt]
        l_ne = [self.lat + 1, self.lon, self.alt]
        self.assertTrue(l_eq == point)
        self.assertTrue(point == l_eq)
        self.assertFalse(l_eq != point)
        self.assertFalse(point != l_eq)

        self.assertFalse(l_ne == point)
        self.assertFalse(point == l_ne)
        self.assertTrue(l_ne != point)
        self.assertTrue(point != l_ne)

    def test_point_comparison_ignores_strings(self):
        point = Point("1", "2", "3")
        self.assertFalse(point == "123")
        self.assertTrue(point != "123")
        self.assertTrue(point == (1, 2, 3))

    def test_point_is_picklable(self):
        point = Point(self.lat, self.lon, self.alt)
        # https://docs.python.org/2/library/pickle.html#data-stream-format
        for protocol in (0, 1, 2, -1):
            pickled = pickle.dumps(point, protocol=protocol)
            point_unp = pickle.loads(pickled)
            self.assertEqual(point, point_unp)
            self.assertEqual(self.coords, point_unp)
