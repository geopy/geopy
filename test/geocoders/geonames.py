# -*- coding: UTF-8 -*-
import unittest

from pytz import timezone

from geopy import Point
from geopy.compat import u
from geopy.geocoders import GeoNames
from test.geocoders.util import GeocoderTestBase, env


class GeoNamesTestCaseUnitTest(GeocoderTestBase):

    def test_user_agent_custom(self):
        geocoder = GeoNames(
            username='DUMMYUSER_NORBERT',
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')


@unittest.skipUnless(
    bool(env.get('GEONAMES_USERNAME')),
    "No GEONAMES_USERNAME env variable set"
)
class GeoNamesTestCase(GeocoderTestBase):

    delta = 0.04
    new_york_point = Point(40.75376406311989, -73.98489005863667)
    america_new_york = timezone("America/New_York")

    @classmethod
    def setUpClass(cls):
        cls.geocoder = GeoNames(username=env['GEONAMES_USERNAME'])

    def reverse_timezone_run(self, payload, expected):
        timezone = self._make_request(self.geocoder.reverse_timezone, **payload)
        self.assertEqual(timezone.pytz_timezone, expected)
        return timezone

    def test_unicode_name(self):
        self.geocode_run(
            {"query": "Mount Everest, Nepal"},
            {"latitude": 27.987, "longitude": 86.925},
            skiptest_on_failure=True,  # sometimes the result is empty
        )

    def test_query_urlencoding(self):
        location = self.geocode_run(
            {"query": u("Ry\u016b\u014d")},
            {"latitude": 35.65, "longitude": 138.5},
            skiptest_on_failure=True,  # sometimes the result is empty
        )
        self.assertIn(u("Ry\u016b\u014d"), location.address)

    def test_reverse(self):
        self.reverse_run(
            {"query": "40.75376406311989, -73.98489005863667", "exactly_one": True},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

        self.assertRaises(
            ValueError,
            self._make_request,
            self.geocoder.reverse,
            **{"query": "40.75376406311989, -73.98489005863667",
               "exactly_one": True,
               "find_nearby_type": "findNearbyJSON",
               "lang": 'en'}
        )

        self.assertRaises(
            ValueError,
            self._make_request,
            self.geocoder.reverse,
            **{"query": "40.75376406311989, -73.98489005863667",
               "exactly_one": True,
               "feature_code": 'ADM1'}
        )

    def test_reverse_timezone(self):
        self.reverse_timezone_run(
            {"query": self.new_york_point},
            self.america_new_york,
        )
