# -*- coding: UTF-8 -*-
import unittest

import pytz

from geopy import Point
from geopy.compat import u
from geopy.exc import GeocoderQueryError
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
        location = self.reverse_run(
            {
                "query": "40.75376406311989, -73.98489005863667",
                "exactly_one": True,
            },
            {
                "latitude": 40.75376406311989,
                "longitude": -73.98489005863667,
            },
        )
        self.assertIn("Times Square", location.address)

    def test_reverse_nearby_place_name_raises_for_feature_code(self):
        with self.assertRaises(ValueError):
            self.reverse_run(
                {
                    "query": "40.75376406311989, -73.98489005863667",
                    "exactly_one": True,
                    "feature_code": "ADM1",
                },
                {},
            )

        with self.assertRaises(ValueError):
            self.reverse_run(
                {
                    "query": "40.75376406311989, -73.98489005863667",
                    "exactly_one": True,
                    "feature_code": "ADM1",
                    "find_nearby_type": "findNearbyPlaceName",
                },
                {},
            )

    def test_reverse_nearby_place_name_lang(self):
        location = self.reverse_run(
            {
                "query": "52.50, 13.41",
                "exactly_one": True,
                "lang": 'ru',
            },
            {},
        )
        self.assertIn('Берлин, Германия', location.address)

    def test_reverse_find_nearby_raises_for_lang(self):
        with self.assertRaises(ValueError):
            self.reverse_run(
                {
                    "query": "40.75376406311989, -73.98489005863667",
                    "exactly_one": True,
                    "find_nearby_type": 'findNearby',
                    "lang": 'en',
                },
                {},
            )

    def test_reverse_find_nearby(self):
        location = self.reverse_run(
            {
                "query": "40.75376406311989, -73.98489005863667",
                "exactly_one": True,
                "find_nearby_type": 'findNearby',
            },
            {
                "latitude": 40.75376406311989,
                "longitude": -73.98489005863667,
            },
        )
        self.assertIn("New York, United States", location.address)

    def test_reverse_find_nearby_feature_code(self):
        self.reverse_run(
            {
                "query": "40.75376406311989, -73.98489005863667",
                "exactly_one": True,
                "find_nearby_type": 'findNearby',
                "feature_code": "ADM1",
            },
            {
                "latitude": 40.16706,
                "longitude": -74.49987,
            },
        )

    def test_reverse_raises_for_unknown_find_nearby_type(self):
        with self.assertRaises(GeocoderQueryError):
            self.reverse_run(
                {
                    "query": "40.75376406311989, -73.98489005863667",
                    "exactly_one": True,
                    "find_nearby_type": "findSomethingNonExisting",
                },
                {},
            )

    def test_reverse_timezone(self):
        new_york_point = Point(40.75376406311989, -73.98489005863667)
        america_new_york = pytz.timezone("America/New_York")

        timezone = self.reverse_timezone_run(
            {"query": new_york_point},
            america_new_york,
        )
        self.assertEqual(timezone.raw['countryCode'], 'US')
