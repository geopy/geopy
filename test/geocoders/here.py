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
            app_id=env['HERE_APP_ID'],
            app_code=env['HERE_APP_CODE'],
            timeout=10,
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
        Here.geocode unicode in Japanese for Paris. (POIs not included.)
        """
        self.geocode_run(
            {"query": u("\u30d1\u30ea")},
            {"latitude": 48.85718, "longitude": 2.34141}
        )

    def test_bbox(self):
        self.geocode_run(
            {"query": "moscow",  # Idaho USA
             "bbox": [[50.1, -130.1], [44.1, -100.9]]},
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )

    def test_mapview(self):
        self.geocode_run(
            {"query": "moscow",  # Idaho USA
             "mapview": [[50.1, -130.1], [44.1, -100.9]]},
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )

    def test_geocode_shapes(self):
        """
        Here.geocode using additional data parameter (postal code shapes)
        """
        address_string = "435 north michigan ave, chicago il 60611 usa"
        res = self.geocode_run(
            {"query": address_string, "additional_data": "IncludeShapeLevel,postalCode"},
            {"latitude": 41.89035, "longitude": -87.62333},
        )
        shape_value = res.raw['Location']['Shape']['Value']
        self.assertTrue(shape_value.startswith('MULTIPOLYGON ((('))

    def test_geocode_with_language_de(self):
        """
        Here.geocode using language parameter to get a non-English response
        """
        address_string = "435 north michigan ave, chicago il 60611 usa"
        res = self.geocode_run(
            {"query": address_string, "language": "de-DE"},
            {}
        )
        self.assertIn("Vereinigte Staaten", res.address)

    def test_geocode_with_language_en(self):
        """
        Here.geocode using language parameter to get an English response
        """
        address_string = "435 north michigan ave, chicago il 60611 usa"
        res = self.geocode_run(
            {"query": address_string, "language": "en-US"},
            {}
        )
        self.assertIn("United States", res.address)

    def test_geocode_with_paging(self):
        """
        Here.geocode using simple paging "ouside" geopy
        """
        address_string = "Hauptstr., Berlin, Germany"
        input = {"query": address_string, "maxresults": 12, "exactly_one": False}
        res = self.geocode_run(input, {})
        self.assertEqual(len(res), 12)

        input["pageinformation"] = 2
        res = self.geocode_run(input, {})
        self.assertEqual(len(res), 3)

        input["pageinformation"] = 3
        res = self.geocode_run(input, {}, expect_failure=True)

    def test_reverse(self):
        self.reverse_run(
            {"query": Point(40.753898, -73.985071)},
            {"latitude": 40.753898, "longitude": -73.985071}
        )

    def test_reverse_point_radius_1000_float(self):
        """
        Here.reverse Point with radius
        """
        # needs more testing
        res = self.reverse_run(
            {"query": Point(40.753898, -73.985071), "radius": 1000.12,
             "exactly_one": False},
            {"latitude": 40.753898, "longitude": -73.985071}
        )
        self.assertGreater(len(res), 5)

    def test_reverse_point_radius_10(self):
        """
        Here.reverse Point with radius
        """
        # needs more testing
        res = self.reverse_run(
            {"query": Point(40.753898, -73.985071), "radius": 10, "exactly_one": False},
            {"latitude": 40.753898, "longitude": -73.985071}
        )
        self.assertGreater(len(res), 5)

    def test_reverse_with_language_de(self):
        """
        Here.reverse using point and language parameter to get a non-English response
        """
        res = self.reverse_run(
            {"query": Point(40.753898, -73.985071), "language": "de-DE"},
            {}
        )
        self.assertIn("Vereinigte Staaten", res.address)

    def test_reverse_with_language_en(self):
        """
        Here.reverse using point and language parameter to get an English response
        """
        res = self.reverse_run(
            {"query": Point(40.753898, -73.985071), "language": "en-US"},
            {}
        )
        self.assertIn("United States", res.address)

    def test_reverse_with_mode_areas(self):
        """
        Here.reverse using mode parameter 'retrieveAreas'.
        """
        res = self.reverse_run(
            {"query": Point(40.753898, -73.985071), "mode": "retrieveAreas"},
            {}
        )
        self.assertIn("Theater District-Times Square", res.address)

    def test_reverse_with_maxresults_5(self):
        """
        Here.reverse using maxresults parameter 5.
        """
        res = self.reverse_run(
            {
                "query": Point(40.753898, -73.985071),
                "maxresults": 5,
                "exactly_one": False
            },
            {}
        )
        self.assertEqual(len(res), 5)
