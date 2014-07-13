import unittest
from geopy.geocoders.opencage import OpenCage

class TestOpenCage(unittest.TestCase):

    def test_opencage(self):
        api='ad25821727cf9b6f2df5437745f82453'
        c = OpenCage(api_key=api, timeout=5)
        l = c.geocode('Mount View Road, London')
        self.assertEqual(51.5864774, l.latitude)
        rl = c.reverse(l.point)
        self.assertTrue('London Borough of Brent' in rl[0].address)

if __name__ == '__main__':
    unittest.main()

