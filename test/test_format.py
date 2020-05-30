import pytest

from geopy.format import format_degrees
from geopy.point import Point


@pytest.mark.xfail
def test_format():
    assert (
        format_degrees(Point.parse_degrees('-13', '19', 0)) ==
        "-13 19\' 0.0\""
    )
