import math
import pickle
import sys
import unittest
import warnings

from geopy.point import Point


class PointTestCase(unittest.TestCase):
    lat = 40.74113
    lon = -73.989656
    alt = 3
    coords = (lat, lon, alt)

    def test_point_float(self):
        point = Point(self.lat, self.lon, self.alt)
        self.assertEqual(point.longitude, self.lon)
        self.assertEqual(point.latitude, self.lat)
        self.assertEqual(point.altitude, self.alt)

    def test_point_str_simple(self):
        for each in ("%s,%s", "%s %s", "%s;%s"):
            point = Point(each % (self.lat, self.lon))
            self.assertEqual(point.longitude, self.lon)
            self.assertEqual(point.latitude, self.lat)
            self.assertEqual(point.altitude, 0)

    def test_point_str_deg(self):
        point = Point("UT: N 39\xb020' 0'' / W 74\xb035' 0''")
        self.assertEqual(point.latitude, 39.333333333333336)
        self.assertEqual(point.longitude, -74.58333333333333)
        self.assertEqual(point.altitude, 0)

    def test_point_format(self):
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

        with self.assertRaises(ValueError):
            # It could be interpreted as `Point(75, 5)`.
            Point("75 5th Avenue, NYC, USA")

    def test_point_from_string(self):
        # Examples are from the docstring of `Point.from_string`.
        self.assertEqual(Point("41.5;-81.0"), (41.5, -81.0, 0.0))
        self.assertEqual(Point("41.5,-81.0"), (41.5, -81.0, 0.0))
        self.assertEqual(Point("41.5 -81.0"), (41.5, -81.0, 0.0))
        self.assertEqual(Point("+41.5 -81.0"), (41.5, -81.0, 0.0))
        self.assertEqual(Point("+41.5 +81.0"), (41.5, 81.0, 0.0))
        self.assertEqual(Point("41.5 N -81.0 W"), (41.5, 81.0, 0.0))
        self.assertEqual(Point("-41.5 S;81.0 E"), (41.5, 81.0, 0.0))
        self.assertEqual(Point("23 26m 22s N 23 27m 30s E"),
                         (23.439444444444444, 23.458333333333332, 0.0))
        self.assertEqual(Point("23 26' 22\" N 23 27' 30\" E"),
                         (23.439444444444444, 23.458333333333332, 0.0))
        self.assertEqual(Point("UT: N 39\xb020' 0'' / W 74\xb035' 0''"),
                         (39.333333333333336, -74.58333333333333, 0.0))

    def test_point_format_altitude(self):
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
        with self.assertRaises(ValueError):
            Point([1])
        self.assertEqual(Point(0, 0, 0), Point([]))

        with self.assertRaises(ValueError):
            Point([1, 2, 3, 4])

    def test_point_from_single_number(self):
        with self.assertRaises(ValueError):
            # Point from a single number is probably a misuse,
            # thus it's discouraged.
            Point(5)

        # But an explicit zero longitude is fine
        self.assertEqual((5, 0, 0), tuple(Point(5, 0)))

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
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            with self.assertRaises(ValueError):
                # Latitude normalization is not allowed
                Point(95, 185, 375)
            self.assertEqual(1, len(w))

            with self.assertRaises(ValueError):
                # Latitude normalization is not allowed
                Point(-95, -185, 375)
            self.assertEqual(2, len(w))

            point = Point(-85, 185, 375)
            self.assertEqual((-85, -175, 375), tuple(point))

            point = Point(85, -185, 375)
            self.assertEqual((85, 175, 375), tuple(point))

            # note that the zeros might be negative
            point = Point(-0.0, -0.0, 375)
            self.assertEqual((0.0, 0.0, 375.0), tuple(point))
            # ensure that negative zeros are normalized to the positive ones
            self.assertEqual((1.0, 1.0, 1.0), tuple(math.copysign(1.0, x) for x in point))

            point = Point(90, 180, 375)
            self.assertEqual((90, 180, 375), tuple(point))
            point = Point(-90, -180, 375)
            self.assertEqual((-90, -180, 375), tuple(point))
            self.assertEqual(2, len(w))

            point = Point(-90, -540, 375)
            self.assertEqual((-90, -180, 375), tuple(point))

            point = Point(90, 540, 375)
            self.assertEqual((90, -180, 375), tuple(point))
            self.assertEqual(2, len(w))

    def test_point_degrees_normalization_does_not_lose_precision(self):
        if sys.float_info.mant_dig != 53:  # pragma: no cover
            raise unittest.SkipTest('This platform does not store floats as '
                                    'IEEE 754 double')
        # IEEE 754 double is stored like this:
        # sign (1 bit) | exponent (11 bit) | fraction (52 bit)
        # \/         \/
        # 0100000111010010011001001001001011000010100000000000000000000000
        #
        # The issue is that there might be a loss in precision during
        # normalization.
        # For example, 180.00000000000003 is stored like this:
        # \/         \/
        # 0100000001100110100000000000000000000000000000000000000000000001
        #
        # And if we do (180.00000000000003 + 180 - 180), then we would get
        # exactly 180.0:
        # 0100000001100110100000000000000000000000000000000000000000000000
        #
        # Notice that the last fraction bit has been lost, because
        # (180.00000000000003 + 180) fraction doesn't fit in 52 bits.
        #
        # This test ensures that such unwanted precision loss is not happening.
        self.assertEqual(tuple(Point(-89.99999999999998, 180.00000000000003)),
                         (-89.99999999999998, -179.99999999999997, 0))
        self.assertEqual(tuple(Point(9.000000000000002, 1.8000000000000003)),
                         (9.000000000000002, 1.8000000000000003, 0))

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

    def test_point_setitem_normalization(self):
        point = Point()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            with self.assertRaises(ValueError):
                point[0] = 100
            self.assertEqual(1, len(w))
            self.assertEqual((0, 0, 0), tuple(point))
            point[0] = -80
            point[1] = 200
            # Please note that attribute assignments are not normalized.
            # Only __setitem__ assignments are.
            self.assertEqual((-80, -160, 0), tuple(point))
            with self.assertRaises(ValueError):
                point[1] = float("nan")
            self.assertEqual(1, len(w))
            self.assertEqual((-80, -160, 0), tuple(point))

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
        self.assertEqual(
            Point(self.lat, self.lon),
            Point("%s %s" % (self.lat, self.lon))
        )

    def test_point_ne(self):
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
