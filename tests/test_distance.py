import math

from nose.tools import assert_raises, assert_almost_equal

from geopy.point import Point
from geopy.distance import GreatCircleDistance, VincentyDistance, EARTH_RADIUS


EARTH_CIRCUMFERENCE = 2 * math.pi * EARTH_RADIUS
NORTH_POLE = Point(90, 0)
SOUTH_POLE = Point(-90, 0)


class CommonDistanceCases:
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

    def test_should_not_converge_for_half_trip_around_equator(self):
        assert_raises(ValueError, self.cls, (0, 0), (0, 180))

    def test_should_compute_destination_for_half_trip_around_equator(self):
        distance = self.cls(EARTH_CIRCUMFERENCE / 2)
        destination = distance.destination((0, 0), 0)
        assert_almost_equal(destination.latitude, 0, 0)
        assert_almost_equal(destination.longitude, -180, 0)

