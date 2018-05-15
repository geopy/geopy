
import unittest

from geopy.format import format_degrees
from geopy.point import Point


class TestFormat(unittest.TestCase):

    @unittest.skip("")
    def test_format(self):
        """
        format_degrees
        """
        self.assertEqual(
            format_degrees(Point.parse_degrees('-13', '19', 0)),
            "-13 19\' 0.0\""
        )
