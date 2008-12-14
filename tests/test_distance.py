import math

from nose.tools import assert_raises, assert_almost_equal

from geopy.point import Point
from geopy.distance import (Distance,
                            GreatCircleDistance,
                            VincentyDistance,
                            EARTH_RADIUS,
                            ELLIPSOIDS)


EARTH_CIRCUMFERENCE = 2 * math.pi * EARTH_RADIUS
NORTH_POLE = Point(90, 0)
SOUTH_POLE = Point(-90, 0)


class CommonDistanceComputationCases:
    def test_should_have_length_when_only_given_length(self):
        distance = 1
        assert self.cls(distance).kilometers == distance

    def test_should_have_zero_distance_for_coincident_points(self):
        assert self.cls((0, 0), (0, 0)).kilometers == 0

    def test_should_have_nonzero_distance_for_distinct_points(self):
        assert self.cls((0, 0), (0, 1)).kilometers > 0

    def test_should_compute_distance_for_trip_between_poles(self):
        distance = self.cls(SOUTH_POLE, NORTH_POLE)
        expected_distance = EARTH_CIRCUMFERENCE / 2
        assert_almost_equal(distance.kilometers, expected_distance, -2)

    def test_should_compute_destination_for_trip_between_poles(self):
        distance = self.cls(EARTH_CIRCUMFERENCE / 2)
        destination = distance.destination(NORTH_POLE, 0)
        assert_almost_equal(destination.latitude, -90, 0)
        assert_almost_equal(destination.longitude, 0)

    def test_should_recognize_equivalence_of_pos_and_neg_180_longitude(self):
        distance = self.cls((0, 180), (0, -180)).kilometers
        assert_almost_equal(distance, 0)


class CommonMathematicalOperatorCases:
    def test_should_be_able_to_add_distances(self):
        added = self.cls(1.0) + self.cls(1.0)
        assert_almost_equal(added.kilometers, 2.0)

    def test_should_not_allow_adding_with_objects_that_arent_distances(self):
        assert_raises(TypeError, lambda: self.cls(1.0) + 5)

    def test_should_be_able_to_negate_distances(self):
        distance = self.cls(1.0)
        assert_almost_equal(-(distance.kilometers),
                            (-distance).kilometers)

    def test_should_be_able_to_subtract_distances(self):
        subtracted = self.cls(2.0) - self.cls(1.0)
        assert_almost_equal(subtracted.kilometers, 1)

    def test_should_be_able_to_multiply_distances_by_floats(self):
        assert_almost_equal((self.cls(2.0) * 2.0).kilometers,
                            4.0)

    def test_should_not_be_able_to_multiply_distances_by_distances(self):
        assert_raises(TypeError, lambda: self.cls(1.0) * self.cls(2.0))

    def test_should_be_able_to_divide_distances_by_distances(self):
        ratio = self.cls(4.0) / self.cls(2.0)
        assert_almost_equal(ratio, 2.0)

    def test_should_be_able_to_divide_distances_by_floats(self):
        divided_distance = self.cls(4.0) / 2.0
        assert_almost_equal(divided_distance.kilometers, 2.0)

    def test_should_be_able_to_take_absolute_value_of_distances(self):
        assert_almost_equal(abs(self.cls(-1.0)).kilometers,
                            1.0)

    def test_should_be_true_in_boolean_context_when_nonzero_length(self):
        assert self.cls(1.0)

    def test_should_be_false_in_boolean_context_when_zero_length(self):
        assert not self.cls(0)

    def test_should_get_consistent_results_for_distance_calculations(self):
        distance1, distance2 = [self.cls((0, 0), (0, 1))
                                for _ in range(2)]
        assert distance1.kilometers == distance2.kilometers


class CommonConversionCases:
    def test_should_convert_to_kilometers(self):
        assert self.cls(1.0).kilometers == 1.0

    def test_should_convert_to_kilometers_with_abbreviation(self):
        assert self.cls(1.0).km == 1.0

    def test_should_convert_to_meters(self):
        assert self.cls(1.0).meters == 1000.0

    def test_should_convert_to_meters_with_abbreviation(self):
        assert self.cls(1.0).m == 1000.0

    def test_should_convert_to_miles(self):
        assert_almost_equal(self.cls(1.0).miles, 0.621371192)

    def test_should_convert_to_miles_with_abbreviation(self):
        assert_almost_equal(self.cls(1.0).mi, 0.621371192)

    def test_should_convert_to_feet(self):
        assert_almost_equal(self.cls(1.0).feet, 3280.8399, 4)

    def test_should_convert_to_feet_with_abbreviation(self):
        assert_almost_equal(self.cls(1.0).ft, 3280.8399, 4)

    def test_should_convert_to_nautical_miles(self):
        assert_almost_equal(self.cls(1.0).nautical, 0.539956803)

    def test_should_convert_to_nautical_miles_with_abbrevation(self):
        assert_almost_equal(self.cls(1.0).nm, 0.539956803)


class CommonDistanceCases(CommonDistanceComputationCases,
                          CommonMathematicalOperatorCases,
                          CommonConversionCases):
    pass


class TestWhenInstantiatingBaseDistanceClass:
    def test_should_not_be_able_to_give_multiple_points(self):
        assert_raises(NotImplementedError, lambda: Distance(1, 2, 3, 4))


class TestWhenComputingGreatCircleDistance(CommonDistanceCases):
    cls = GreatCircleDistance

    def test_should_compute_distance_for_half_trip_around_equator(self):
        distance_around_earth = self.cls((0, 0), (0, 180)).kilometers
        assert distance_around_earth == EARTH_CIRCUMFERENCE / 2

    def test_should_compute_destination_for_half_trip_around_equator(self):
        distance = self.cls(EARTH_CIRCUMFERENCE / 2)
        destination = distance.destination((0, 0), 0)
        assert_almost_equal(destination.latitude, 0)
        assert_almost_equal(destination.longitude, 180)


class TestWhenComputingVincentyDistance(CommonDistanceCases):
    cls = VincentyDistance

    def setup(self):
        self.original_ellipsoid = self.cls.ELLIPSOID

    def teardown(self):
        self.cls.ELLIPSOID = self.original_ellipsoid

    def test_should_not_converge_for_half_trip_around_equator(self):
        assert_raises(ValueError, self.cls, (0, 0), (0, 180))

    def test_should_compute_destination_for_half_trip_around_equator(self):
        distance = self.cls(EARTH_CIRCUMFERENCE / 2)
        destination = distance.destination((0, 0), 0)
        assert_almost_equal(destination.latitude, 0, 0)
        assert_almost_equal(destination.longitude, -180, 0)

    def test_should_get_distinct_results_for_different_ellipsoids(self):
        results = []
        for ellipsoid_name in ELLIPSOIDS.keys():
            self.cls.ELLIPSOID = ELLIPSOIDS[ellipsoid_name]
            results.append(self.cls((0, 0), (0, 1)))

        assert not any(results[x].kilometers == results[y].kilometers
                       for x in range(len(results))
                       for y in range(len(results))
                       if x != y)

