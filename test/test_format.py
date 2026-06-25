import pytest

from geopy.format import format_degrees
from geopy.point import Point


@pytest.mark.parametrize(
    "input, expected",
    [
        (("12", "30", 0), "12 30' 0\""),
        (("12", "30", "30"), "12 30' 30\""),
        (("12", "30", 30.4), "12 30' 30.4\""),
    ],
)
def test_format_simple(input, expected):
    assert format_degrees(Point.parse_degrees(*input)) == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        (("13", "20", 0), "13 20' 0\""),
        (("-13", "19", 0), "-13 19' 0\""),
    ],
)
def test_format_float_precision(input, expected):
    assert format_degrees(Point.parse_degrees(*input)) == expected
