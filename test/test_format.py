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


# These tests currently fail, because conversion to degrees (as float)
# causes loss in precision (mostly because of divisions by 3):
@pytest.mark.xfail
@pytest.mark.parametrize(
    "input, expected",
    [
        (("13", "20", 0), "13 20' 0\""),  # actual: `13 20' 2.13163e-12"`
        (("-13", "19", 0), "-13 19' 0\""),  # actual: `-13 18' 60"`
    ],
)
def test_format_float_precision(input, expected):
    assert format_degrees(Point.parse_degrees(*input)) == expected
