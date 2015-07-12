
import unittest2 as unittest

from geopy.compat import u
from geopy.point import Point
from geopy.exc import GeocoderQueryError
from geopy.geocoders import DataBC
from test.geocoders.util import GeocoderTestBase, env


class DataBCTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = DataBC()

    def test_geocode(self):
        """
        DataBC.geocode
        """
        res = self._make_request(
            self.geocoder.geocode,
            "135 North Pym Road, Parksville"
        )
        self.assertAlmostEqual(res.latitude, 49.321, delta=self.delta)
        self.assertAlmostEqual(res.longitude, -124.337, delta=self.delta)

    def test_unicode_name(self):
        """
        DataBC.geocode unicode
        """
        res = self._make_request(
            self.geocoder.geocode,
            u("Barri\u00e8re"),
        )
        self.assertAlmostEqual(res.latitude, 51.179, delta=self.delta)
        self.assertAlmostEqual(res.longitude, -120.123, delta=self.delta)

    def test_multiple_results(self):
        """
        DataBC.geocode with multiple results
        """
        res = self._make_request(
            self.geocoder.geocode,
            "1st St",
            exactly_one=False
        )

        self.assertGreater(len(res), 1)

    def test_optional_params(self):
        """
        DataBC.geocode using optional params
        """

        res = self._make_request(
            self.geocoder.geocode,
            "5670 malibu terrace nanaimo bc",
            location_descriptor="accessPoint",
            set_back=100
        )
        self.assertAlmostEqual(res.latitude, 49.2299, delta=self.delta)
        self.assertAlmostEqual(res.longitude, -124.0163, delta=self.delta)

    def test_query_error(self):
        """
        DataBC.geocode with bad query parameters
        """
        with self.assertRaises(GeocoderQueryError):
          res = self._make_request(
              self.geocoder.geocode,
              "1 Main St, Vancouver",
              location_descriptor="access_Point",
          )
