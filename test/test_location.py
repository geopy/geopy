# encoding: utf-8
"""
Test Location.
"""

import unittest
from geopy.compat import u, py3k
from geopy.location import Location
from geopy.point import Point


GRAND_CENTRAL_STR = "89 E 42nd St New York, NY 10017"

GRAND_CENTRAL_COORDS_STR = "40.752662,-73.9773"
GRAND_CENTRAL_COORDS_TUPLE = (40.752662, -73.9773, 0)
GRAND_CENTRAL_POINT = Point(GRAND_CENTRAL_COORDS_STR)

GRAND_CENTRAL_RAW = {
    'id': '1',
    'class': 'place',
    'lat': '40.752662',
    'lon': '-73.9773',
    'display_name':
        "89, East 42nd Street, New York, "
        "New York, 10017, United States of America",
}


class LocationTestCase(unittest.TestCase): # pylint: disable=R0904
    """
    Test :class:`geopy.location.Location`.
    """

    def _location_iter_test(self,
            loc,
            ref_address=GRAND_CENTRAL_STR,
            ref_longitude=GRAND_CENTRAL_COORDS_TUPLE[0],
            ref_latitude=GRAND_CENTRAL_COORDS_TUPLE[1]
        ):
        """
        Helper for equality tests on Location's __iter__.
        """
        address, (latitude, longitude) = loc
        self.assertEqual(address, ref_address)
        self.assertEqual(latitude, ref_longitude)
        self.assertEqual(longitude, ref_latitude)

    def _location_properties_test(self, loc, raw=None):
        """
        Helper for equality tests of Location's properties
        """
        self.assertEqual(loc.address, GRAND_CENTRAL_STR)
        self.assertEqual(loc.latitude, GRAND_CENTRAL_COORDS_TUPLE[0])
        self.assertEqual(loc.longitude, GRAND_CENTRAL_COORDS_TUPLE[1])
        self.assertEqual(loc.altitude, GRAND_CENTRAL_COORDS_TUPLE[2])
        if raw is not None:
            self.assertEqual(loc.raw, raw)

    def test_location_init(self):
        """
        Location with string point
        """
        loc = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_COORDS_STR)
        self._location_iter_test(loc)
        self.assertEqual(loc.point, GRAND_CENTRAL_POINT)

    def test_location_point(self):
        """
        Location with Point
        """
        loc = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT)
        self._location_iter_test(loc)
        self.assertEqual(loc.point, GRAND_CENTRAL_POINT)

    def test_location_none(self):
        """
        Location with None point
        """
        loc = Location(GRAND_CENTRAL_STR, None)
        self._location_iter_test(loc, GRAND_CENTRAL_STR, None, None)
        self.assertEqual(loc.point, None)

    def test_location_iter(self):
        """
        Location with iterable point
        """
        loc = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_COORDS_TUPLE)
        self._location_iter_test(loc)
        self.assertEqual(loc.point, GRAND_CENTRAL_POINT)

    def test_location_typeerror(self):
        """
        Location invalid point TypeError
        """
        with self.assertRaises(TypeError):
            Location(GRAND_CENTRAL_STR, 1)

    def test_location_array_access(self):
        """
        Location array access
        """
        loc = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_COORDS_TUPLE)
        self.assertEqual(loc[0], GRAND_CENTRAL_STR)
        self.assertEqual(loc[1][0], GRAND_CENTRAL_COORDS_TUPLE[0])
        self.assertEqual(loc[1][1], GRAND_CENTRAL_COORDS_TUPLE[1])

    def test_location_properties(self):
        """
        Location properties
        """
        loc = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT)
        self._location_properties_test(loc)

    def test_location_raw(self):
        """
        Location.raw
        """
        loc = Location(
            GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT, raw=GRAND_CENTRAL_RAW
        )
        self._location_properties_test(loc, GRAND_CENTRAL_RAW)

    def test_location_string(self):
        """
        str(Location) == Location.address
        """
        loc = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT)
        self.assertEqual(str(loc), loc.address)

    def test_location_len(self):
        """
        len(Location)
        """
        loc = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT)
        self.assertEqual(len(loc), 2)

    def test_location_eq(self):
        """
        Location.__eq__
        """
        loc1 = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT)
        loc2 = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_COORDS_TUPLE)
        self.assertEqual(loc1, loc2)

    def test_location_ne(self):
        """
        Location.__ne__
        """
        loc1 = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT)
        loc2 = Location(GRAND_CENTRAL_STR, None)
        self.assertNotEqual(loc1, loc2)

    def test_location_repr(self):
        """
        Location.__repr__ string and unicode
        """
        address = u(
            "22, Ksi\u0119dza Paw\u0142a Po\u015bpiecha, "
            "Centrum Po\u0142udnie, Zabrze, wojew\xf3dztwo "
            "\u015bl\u0105skie, 41-800, Polska"
        )
        point = (0.0, 0.0, 0.0)
        loc = Location(address, point)
        if py3k:
            self.assertEqual(
                repr(loc),
                "Location(%s, %r)" % (address, point)
            )
        else:
            self.assertEqual(
                repr(loc),
                "Location((%s, %s, %s))" % point
            )

