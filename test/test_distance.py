import math
import unittest
import warnings

from geopy.distance import (
    EARTH_RADIUS,
    Distance,
    GeodesicDistance,
    GreatCircleDistance,
    distance,
    lonlat,
)
from geopy.point import Point

EARTH_CIRCUMFERENCE = 2 * math.pi * EARTH_RADIUS
NORTH_POLE = Point(90, 0)
SOUTH_POLE = Point(-90, 0)
FIJI = Point(-16.1333333, 180.0)  # Vunikondi, Fiji


class CommonDistanceComputationCases:

    cls = None

    def test_zero_measure(self):
        self.cls(
            (40.753152999999998, -73.982275999999999),
            (40.753152999999998, -73.982275999999999)
        )

    def test_should_have_length_when_only_given_length(self):
        distance = 1
        self.assertEqual(self.cls(distance).kilometers, distance)

    def test_should_have_zero_distance_for_coincident_points(self):
        self.assertEqual(self.cls((0, 0), (0, 0)).kilometers, 0)

    def test_should_have_nonzero_distance_for_distinct_points(self):
        self.assertTrue(self.cls((0, 0), (0, 1)).kilometers > 0)

    def test_max_longitude(self):
        distance = self.cls(kilometers=1.0)
        destination = distance.destination(FIJI, 45)
        self.assertAlmostEqual(destination.longitude, -179.99338, 4)

    def test_should_compute_distance_for_trip_between_poles(self):
        distance = self.cls(SOUTH_POLE, NORTH_POLE)
        expected_distance = EARTH_CIRCUMFERENCE / 2
        self.assertAlmostEqual(distance.kilometers, expected_distance, -2)

    def test_should_compute_destination_for_trip_between_poles(self):
        distance = self.cls(EARTH_CIRCUMFERENCE / 2)
        destination = distance.destination(NORTH_POLE, 0)
        self.assertAlmostEqual(destination.latitude, -90, 0)
        self.assertAlmostEqual(destination.longitude, 0)

    def test_destination_bearing_east(self):
        distance = self.cls(kilometers=100)
        for EAST in (90, 90 + 360, -360+90):
            p = distance.destination(Point(0, 160), bearing=EAST)
            self.assertAlmostEqual(p.latitude, 0)
            self.assertAlmostEqual(p.longitude, 160.8993, delta=1e-3)

            p = distance.destination(Point(60, 160), bearing=EAST)
            self.assertAlmostEqual(p.latitude, 59.9878, delta=1e-3)
            self.assertAlmostEqual(p.longitude, 161.79, delta=1e-2)

    def test_should_recognize_equivalence_of_pos_and_neg_180_longitude(self):
        distance1 = self.cls((0, -180), (0, 180)).kilometers
        distance2 = self.cls((0, 180), (0, -180)).kilometers
        self.assertAlmostEqual(distance1, 0)
        self.assertAlmostEqual(distance2, 0)

    def test_should_compute_distance_across_antimeridian(self):
        nines = 1 - 1e-30  # 0.(9)
        distance = self.cls((0, -179 - nines),
                            (0, 179 + nines)).kilometers
        self.assertAlmostEqual(distance, 0)

    def test_should_compute_destination_across_antimeridian(self):
        nines = 1 - 1e-30  # 0.(9)
        distance = self.cls(10)
        point = distance.destination((0, -179 - nines), -90)
        self.assertAlmostEqual(point.latitude, 0.0)
        self.assertAlmostEqual(point.longitude, 179.91, 3)

    def test_should_not_tolerate_nans(self):
        nan = float('nan')
        with self.assertRaises(ValueError):
            self.cls((nan, nan), (1, 1)).kilometers
        with self.assertRaises(ValueError):
            self.cls((nan, 1), (1, nan)).kilometers
        with self.assertRaises(ValueError):
            self.cls((nan, 1), (nan, 1)).kilometers

    def test_should_compute_distance_for_multiple_points_pairwise(self):
        dist_total = self.cls((10, 20), (40, 60), (0, 80), (0, 10))
        dist1 = self.cls((10, 20), (40, 60))
        dist2 = self.cls((40, 60), (0, 80))
        dist3 = self.cls((0, 80), (0, 10))

        self.assertAlmostEqual(dist_total.kilometers,
                               dist1.km + dist2.km + dist3.km)

    def test_should_raise_when_using_single_numbers_as_points(self):
        # Each argument is expected to be a Point. If it's not a point,
        # it will be wrapped in Point.
        # Point(10) equals to Point(10, 0).
        with self.assertRaises(ValueError):
            self.cls(10, 20)

        # no error: explicit tuples are not that suspicious
        self.cls((10, 0), (20, 0))

    def test_should_tolerate_tuples_with_textual_numbers(self):
        dist1 = self.cls(("1", "30"), ("20", "60"))
        dist2 = self.cls((1, 30), (20, 60))
        self.assertAlmostEqual(dist1.kilometers, dist2.kilometers)

    def test_should_warn_for_mixed_up_lat_lon(self):
        lat = 40
        lon = 120  # should exceed max lat (abs 90) to cause a warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            # The correct order is (lat, lon).
            with self.assertRaises(ValueError):
                self.cls((lon, lat), (lon - 10, lat))
            self.assertEqual(1, len(w))

    def test_should_get_consistent_results_for_distance_calculations(self):
        distance1, distance2 = (self.cls((0, 0), (0, 1))
                                for _ in range(2))
        self.assertEqual(distance1.kilometers, distance2.kilometers)


class CommonMathematicalOperatorCases:

    cls = None

    def test_should_be_able_to_add_distances(self):
        added = self.cls(1.0) + self.cls(1.0)
        self.assertAlmostEqual(added.kilometers, 2.0)

    def test_should_not_allow_adding_with_objects_that_arent_distances(self):
        with self.assertRaises(TypeError):
            self.cls(1.0) + 5
        with self.assertRaises(TypeError):
            5 + self.cls(1.0)

    def test_should_be_able_to_negate_distances(self):
        distance = self.cls(1.0)
        self.assertAlmostEqual(-(distance.kilometers),
                               (-distance).kilometers)

    def test_should_be_able_to_subtract_distances(self):
        subtracted = self.cls(2.0) - self.cls(1.0)
        self.assertAlmostEqual(subtracted.kilometers, 1)

    def test_should_be_able_to_multiply_distances_by_floats(self):
        self.assertAlmostEqual((self.cls(2.0) * 2.5).kilometers, 5.0)
        self.assertAlmostEqual((2.5 * self.cls(2.0)).kilometers, 5.0)

    def test_should_not_be_able_to_multiply_distances_by_distances(self):
        with self.assertRaises(TypeError):
            self.cls(1.0) * self.cls(2.0)

    def test_should_not_be_able_to_divide_floats_by_distances(self):
        with self.assertRaises(TypeError):
            1 / self.cls(2.0)
        with self.assertRaises(TypeError):
            1 // self.cls(2.0)

    def test_should_be_able_to_divide_distances_by_distances(self):
        ratio = self.cls(4.0) / self.cls(2.0)
        self.assertIsInstance(ratio, float)
        self.assertAlmostEqual(ratio, 2.0)

    def test_should_be_able_to_floor_divide_distances_by_distances(self):
        ratio = self.cls(4.0) // self.cls(2.0)
        self.assertIsInstance(ratio, float)
        self.assertAlmostEqual(ratio, 2.0)

    def test_should_be_able_to_divide_distances_by_floats(self):
        divided_distance = self.cls(4.0) / 2.0
        self.assertIsInstance(divided_distance, self.cls)
        self.assertAlmostEqual(divided_distance.kilometers, 2.0)

    def test_should_be_able_to_floor_divide_distances(self):
        divided_distance = self.cls(4.0) // 3
        self.assertIsInstance(divided_distance, self.cls)
        self.assertAlmostEqual(divided_distance.kilometers, 1.0)

    def test_should_be_able_to_take_absolute_value_of_distances(self):
        self.assertAlmostEqual(abs(self.cls(-1.0)).kilometers, 1.0)

    def test_should_be_true_in_boolean_context_when_nonzero_length(self):
        self.assertTrue(self.cls(1.0))

    def test_should_be_false_in_boolean_context_when_zero_length(self):
        self.assertFalse(self.cls(0))


class CommonConversionCases:

    cls = None

    def test_should_convert_to_kilometers(self):
        self.assertEqual(self.cls(1.0).kilometers, 1.0)

    def test_should_convert_to_kilometers_with_abbreviation(self):
        self.assertEqual(self.cls(1.0).km, 1.0)

    def test_should_convert_to_meters(self):
        self.assertEqual(self.cls(1.0).meters, 1000.0)

    def test_should_convert_to_meters_with_abbreviation(self):
        self.assertEqual(self.cls(1.0).m, 1000.0)

    def test_should_convert_to_miles(self):
        self.assertAlmostEqual(self.cls(1.0).miles, 0.621371192)

    def test_should_convert_to_miles_with_abbreviation(self):
        self.assertAlmostEqual(self.cls(1.0).mi, 0.621371192)

    def test_should_convert_to_feet(self):
        self.assertAlmostEqual(self.cls(1.0).feet, 3280.8399, 4)

    def test_should_convert_to_feet_with_abbreviation(self):
        self.assertAlmostEqual(self.cls(1.0).ft, 3280.8399, 4)

    def test_should_convert_to_nautical_miles(self):
        self.assertAlmostEqual(self.cls(1.0).nautical, 0.539956803)

    def test_should_convert_to_nautical_miles_with_abbrevation(self):
        self.assertAlmostEqual(self.cls(1.0).nm, 0.539956803)

    def test_should_convert_from_meters(self):
        self.assertEqual(self.cls(meters=1.0).km, 0.001)

    def test_should_convert_from_feet(self):
        self.assertAlmostEqual(self.cls(feet=1.0).km, 0.0003048, 8)

    def test_should_convert_from_miles(self):
        self.assertAlmostEqual(self.cls(miles=1.0).km, 1.6093440)

    def test_should_convert_from_nautical_miles(self):
        self.assertAlmostEqual(self.cls(nautical=1.0).km, 1.8520000)


class CommonComparisonCases:

    cls = None

    def test_should_support_comparison_with_distance(self):
        self.assertTrue(self.cls(1) <= self.cls(1))
        self.assertTrue(self.cls(1) >= self.cls(1))
        self.assertTrue(self.cls(1) < self.cls(2))
        self.assertTrue(self.cls(2) > self.cls(1))
        self.assertTrue(self.cls(1) == self.cls(1))
        self.assertTrue(self.cls(1) != self.cls(2))

        self.assertFalse(self.cls(2) <= self.cls(1))
        self.assertFalse(self.cls(1) >= self.cls(2))
        self.assertFalse(self.cls(2) < self.cls(1))
        self.assertFalse(self.cls(1) > self.cls(2))
        self.assertFalse(self.cls(1) == self.cls(2))
        self.assertFalse(self.cls(1) != self.cls(1))

    def test_should_support_comparison_with_number(self):
        self.assertTrue(1 <= self.cls(1))
        self.assertTrue(1 >= self.cls(1))
        self.assertTrue(1 < self.cls(2))
        self.assertTrue(2 > self.cls(1))
        self.assertTrue(1 == self.cls(1))
        self.assertTrue(1 != self.cls(2))

        self.assertFalse(2 <= self.cls(1))
        self.assertFalse(1 >= self.cls(2))
        self.assertFalse(2 < self.cls(1))
        self.assertFalse(1 > self.cls(2))
        self.assertFalse(1 == self.cls(2))
        self.assertFalse(1 != self.cls(1))


class CommonDistanceCases(CommonDistanceComputationCases,
                          CommonMathematicalOperatorCases,
                          CommonConversionCases,
                          CommonComparisonCases):
    pass


class TestDefaultDistanceClass(CommonMathematicalOperatorCases,
                               CommonConversionCases,
                               CommonComparisonCases,
                               unittest.TestCase):
    cls = Distance

    def test_default_distance(self):
        self.assertEqual(distance(132).km, 132)

    def test_lonlat_function(self):
        newport_ri_xy = (-71.312796, 41.49008)
        point = lonlat(*newport_ri_xy)
        self.assertEqual(point, (41.49008, -71.312796, 0))


class TestWhenComputingGreatCircleDistance(CommonDistanceCases,
                                           unittest.TestCase):
    cls = GreatCircleDistance

    def test_should_compute_distance_for_half_trip_around_equator(self):
        distance_around_earth = self.cls((0, 0), (0, 180)).kilometers
        self.assertEqual(distance_around_earth, EARTH_CIRCUMFERENCE / 2)

    def test_should_compute_destination_for_half_trip_around_equator(self):
        distance = self.cls(EARTH_CIRCUMFERENCE / 2)
        destination = distance.destination((0, 0), 0)
        self.assertAlmostEqual(destination.latitude, 0)
        self.assertAlmostEqual(destination.longitude, 180)

    def test_different_altitudes_error(self):
        with self.assertRaises(ValueError):
            # Different altitudes raise an exception:
            self.cls((10, 10, 10), (20, 20, 15))

        # Equal non-zero altitudes don't raise:
        self.cls((10, 10, 10), (20, 20, 10))


class TestWhenComputingGeodesicDistance(CommonDistanceCases,
                                        unittest.TestCase):

    cls = GeodesicDistance

    def test_different_altitudes_error(self):
        with self.assertRaises(ValueError):
            # Different altitudes raise an exception:
            self.cls((10, 10, 10), (20, 20, 15))

        # Equal non-zero altitudes don't raise:
        self.cls((10, 10, 10), (20, 20, 10))

    def test_miscellaneous_high_accuracy_cases(self):

        testcases = [
          [35.60777, -139.44815, 111.098748429560326,
           -11.17491, -69.95921, 129.289270889708762,
           8935244.5604818305],
          [55.52454, 106.05087, 22.020059880982801,
           77.03196, 197.18234, 109.112041110671519,
           4105086.1713924406],
          [-21.97856, 142.59065, -32.44456876433189,
           41.84138, 98.56635, -41.84359951440466,
           8394328.894657671],
          [-66.99028, 112.2363, 173.73491240878403,
           -12.70631, 285.90344, 2.512956620913668,
           11150344.2312080241],
          [-17.42761, 173.34268, -159.033557661192928,
           -15.84784, 5.93557, -20.787484651536988,
           16076603.1631180673],
          [32.84994, 48.28919, 150.492927788121982,
           -56.28556, 202.29132, 48.113449399816759,
           16727068.9438164461],
          [6.96833, 52.74123, 92.581585386317712,
           -7.39675, 206.17291, 90.721692165923907,
           17102477.2496958388],
          [-50.56724, -16.30485, -105.439679907590164,
           -33.56571, -94.97412, -47.348547835650331,
           6455670.5118668696],
          [-58.93002, -8.90775, 140.965397902500679,
           -8.91104, 133.13503, 19.255429433416599,
           11756066.0219864627],
          [-68.82867, -74.28391, 93.774347763114881,
           -50.63005, -8.36685, 34.65564085411343,
           3956936.926063544],
          [-10.62672, -32.0898, -86.426713286747751,
           5.883, -134.31681, -80.473780971034875,
           11470869.3864563009],
          [-21.76221, 166.90563, 29.319421206936428,
           48.72884, 213.97627, 43.508671946410168,
           9098627.3986554915],
          [-19.79938, -174.47484, 71.167275780171533,
           -11.99349, -154.35109, 65.589099775199228,
           2319004.8601169389],
          [-11.95887, -116.94513, 92.712619830452549,
           4.57352, 7.16501, 78.64960934409585,
           13834722.5801401374],
          [-87.85331, 85.66836, -65.120313040242748,
           66.48646, 16.09921, -4.888658719272296,
           17286615.3147144645],
          [1.74708, 128.32011, -101.584843631173858,
           -11.16617, 11.87109, -86.325793296437476,
           12942901.1241347408],
          [-25.72959, -144.90758, -153.647468693117198,
           -57.70581, -269.17879, -48.343983158876487,
           9413446.7452453107],
          [-41.22777, 122.32875, 14.285113402275739,
           -7.57291, 130.37946, 10.805303085187369,
           3812686.035106021],
          [11.01307, 138.25278, 79.43682622782374,
           6.62726, 247.05981, 103.708090215522657,
           11911190.819018408],
          [-29.47124, 95.14681, -163.779130441688382,
           -27.46601, -69.15955, -15.909335945554969,
           13487015.8381145492]]
        d = self.cls(ellipsoid='WGS-84')
        km = 1000
        for tup in testcases:
            (lat1, lon1, azi1, lat2, lon2, azi2, s12) = tup
            p1, p2 = Point(lat1, lon1), Point(lat2, lon2)
            s12a = d.measure(p1, p2) * km
            self.assertAlmostEqual(s12a, s12, delta=1e-8)
            p = d.destination(p1, azi1, s12/km)
            self.assertAlmostEqual(p.latitude, p2.latitude, delta=1e-13)
            self.assertAlmostEqual(p.longitude, p2.longitude, delta=1e-12)
            p = d.destination(p2, azi2, -s12/km)
            self.assertAlmostEqual(p.latitude, p1.latitude, delta=1e-13)
            self.assertAlmostEqual(p.longitude, p1.longitude, delta=1e-12)


def test_distance_hashing():
    d1 = Distance(1.0)
    d2 = GreatCircleDistance(1.0)
    d3 = GeodesicDistance(1.0)
    assert d1 == d2 == d3
    assert hash(d1) == hash(d2) == hash(d3)
    assert len({d1, d2, d3}) == 1
