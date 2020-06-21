import pickle
import unittest

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


class LocationTestCase(unittest.TestCase):

    def _location_iter_test(
            self,
            loc,
            ref_address=GRAND_CENTRAL_STR,
            ref_longitude=GRAND_CENTRAL_COORDS_TUPLE[0],
            ref_latitude=GRAND_CENTRAL_COORDS_TUPLE[1]
    ):
        address, (latitude, longitude) = loc
        self.assertEqual(address, ref_address)
        self.assertEqual(latitude, ref_longitude)
        self.assertEqual(longitude, ref_latitude)

    def _location_properties_test(self, loc, raw=None):
        self.assertEqual(loc.address, GRAND_CENTRAL_STR)
        self.assertEqual(loc.latitude, GRAND_CENTRAL_COORDS_TUPLE[0])
        self.assertEqual(loc.longitude, GRAND_CENTRAL_COORDS_TUPLE[1])
        self.assertEqual(loc.altitude, GRAND_CENTRAL_COORDS_TUPLE[2])
        if raw is not None:
            self.assertEqual(loc.raw, raw)

    def test_location_str(self):
        loc = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_COORDS_STR, {})
        self._location_iter_test(loc)
        self.assertEqual(loc.point, GRAND_CENTRAL_POINT)

    def test_location_point(self):
        loc = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT, {})
        self._location_iter_test(loc)
        self.assertEqual(loc.point, GRAND_CENTRAL_POINT)

    def test_location_none(self):
        with self.assertRaises(TypeError):
            Location(GRAND_CENTRAL_STR, None, {})

    def test_location_iter(self):
        loc = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_COORDS_TUPLE, {})
        self._location_iter_test(loc)
        self.assertEqual(loc.point, GRAND_CENTRAL_POINT)

    def test_location_point_typeerror(self):
        with self.assertRaises(TypeError):
            Location(GRAND_CENTRAL_STR, 1, {})

    def test_location_array_access(self):
        loc = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_COORDS_TUPLE, {})
        self.assertEqual(loc[0], GRAND_CENTRAL_STR)
        self.assertEqual(loc[1][0], GRAND_CENTRAL_COORDS_TUPLE[0])
        self.assertEqual(loc[1][1], GRAND_CENTRAL_COORDS_TUPLE[1])

    def test_location_properties(self):
        loc = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT, {})
        self._location_properties_test(loc)

    def test_location_raw(self):
        loc = Location(
            GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT, raw=GRAND_CENTRAL_RAW
        )
        self._location_properties_test(loc, GRAND_CENTRAL_RAW)

    def test_location_string(self):
        loc = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT, {})
        self.assertEqual(str(loc), loc.address)

    def test_location_len(self):
        loc = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT, {})
        self.assertEqual(len(loc), 2)

    def test_location_eq(self):
        loc1 = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT, {})
        loc2 = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_COORDS_TUPLE, {})
        self.assertEqual(loc1, loc2)

    def test_location_ne(self):
        loc1 = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT, {})
        loc2 = Location(GRAND_CENTRAL_STR, Point(0, 0), {})
        self.assertNotEqual(loc1, loc2)

    def test_location_repr(self):
        address = (
            "22, Ksi\u0119dza Paw\u0142a Po\u015bpiecha, "
            "Centrum Po\u0142udnie, Zabrze, wojew\xf3dztwo "
            "\u015bl\u0105skie, 41-800, Polska"
        )
        point = (0.0, 0.0, 0.0)
        loc = Location(address, point, {})
        self.assertEqual(
            repr(loc),
            "Location(%s, %r)" % (address, point)
        )

    def test_location_is_picklable(self):
        loc = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT, {})
        # https://docs.python.org/2/library/pickle.html#data-stream-format
        for protocol in (0, 1, 2, -1):
            pickled = pickle.dumps(loc, protocol=protocol)
            loc_unp = pickle.loads(pickled)
            self.assertEqual(loc, loc_unp)

    def test_location_with_unpicklable_raw(self):
        some_class = type('some_class', (object,), {})
        raw_unpicklable = dict(missing=some_class())
        del some_class
        loc_unpicklable = Location(GRAND_CENTRAL_STR, GRAND_CENTRAL_POINT,
                                   raw_unpicklable)
        for protocol in (0, 1, 2, -1):
            with self.assertRaises((AttributeError, pickle.PicklingError)):
                pickle.dumps(loc_unpicklable, protocol=protocol)
