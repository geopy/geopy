# -*- coding: utf-8 -*-

import unittest

from geopy.compat import u
from geopy.geocoders import Here
from geopy.point import Point
from test.geocoders.util import GeocoderTestBase, env


class HereTestCaseUnitTest(GeocoderTestBase):

    def test_user_agent_custom(self):
        geocoder = Here(
            app_id='DUMMYID1234',
            app_code='DUMMYCODE1234',
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')


@unittest.skipUnless(
    bool(env.get('HERE_APP_ID')),
    "No HERE_APP_ID env variable set"
)
@unittest.skipUnless(
    bool(env.get('HERE_APP_CODE')),
    "No HERE_APP_CODE env variable set"
)
class HereTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Here(
            format_string='%s',
            scheme='http',
            app_id=env['HERE_APP_ID'],
            app_code=env['HERE_APP_CODE'],
            timeout=10
        )

    def test_geocode_empty_result(self):
        """
        Here.geocode empty results should be graciously handled.
        """
        self.geocode_run(
            {"query": "xqj37"},
            {},
            expect_failure=True
        )

    def test_geocode(self):
        """
        Here.geocode
        """
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624}
        )

    def test_geocode_structured(self):
        """
        Here.geocode
        """
        query = {
            "street": "north michigan ave",
            "housenumber": "435",
            "city": "chicago",
            "state": "il",
            "postalcode": 60611,
            "country": "usa"
        }
        self.geocode_run(
            {"query": query},
            {"latitude": 41.890, "longitude": -87.624}
        )

    def test_geocode_unicode_name(self):
        """
        Here.geocode unicode in Japanese for Paris ("パリ"). (POIs not included.)
        """
        self.geocode_run(
            {"query": u("\u30d1\u30ea")},
            {"latitude": 48.85718, "longitude": 2.34141}
        )

    def test_geocode_shapes(self):
        """
        Here.geocode using additional data parameter (postal code shapes)
        """
        address_string = "435 north michigan ave, chicago il 60611 usa"
        res = self._make_request(
            self.geocoder.geocode,
            query=address_string,
            additional_data="IncludeShapeLevel,postalCode"
        )
        self.assertAlmostEqual(res.latitude, 41.89035, delta=0.01)
        self.assertAlmostEqual(res.longitude, -87.62333, delta=0.01)
        shape_value = res.raw['Location']['Shape']['Value']
        self.assertTrue(shape_value.startswith('MULTIPOLYGON ((('))

    def test_reverse_string(self):
        """
        Here.reverse string
        """
        self.reverse_run(
            {"query": "40.753898, -73.985071"},
            {"latitude": 40.753898, "longitude": -73.985071}
        )

    def test_reverse_point(self):
        """
        Here.reverse Point
        """
        self.reverse_run(
            {"query": Point(40.753898, -73.985071)},
            {"latitude": 40.753898, "longitude": -73.985071}
        )

    def test_reverse_with_language_de(self):
        """
        Here.reverse using point and language parameter to get a non English response
        """
        res = self._make_request(
            self.geocoder.reverse,
            Point(40.753898, -73.985071),
            language="de-DE"
        )
        self.assertIn("Vereinigte Staaten", res.address)

    def test_reverse_with_language_en(self):
        """
        Here.reverse using point and language parameter to get an English response
        """
        res = self._make_request(
            self.geocoder.reverse,
            Point(40.753898, -73.985071),
            language="en-US"
        )
        self.assertIn("United States", res.address)
