
import unittest
import geopy

class TestFormat(unittest.TestCase):

    def test_format(self):
        d = geopy.point.Point.parse_degrees('-13', '19', 0)
        s = geopy.format.format_degrees(d)
        self.assertEqual("-13 19\' 0.0\"", s)

if __name__ == '__main__':
    unittest.main()

