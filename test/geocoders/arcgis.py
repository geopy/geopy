import unittest
import warnings

from geopy import exc
from geopy.compat import u
from geopy.point import Point
from geopy.geocoders import ArcGIS
from test.geocoders.util import GeocoderTestBase, env


class ArcGISTestCaseUnitTest(GeocoderTestBase):

    def test_user_agent_custom(self):
        geocoder = ArcGIS(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')


class ArcGISTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = ArcGIS(timeout=3)

    def test_config_error(self):
        """
        ArcGIS.__init__ invalid authentication
        """
        with self.assertRaises(exc.ConfigurationError):
            ArcGIS(username='a')

    def test_scheme_config_error(self):
        """
        ArcGIS.__init__ invalid scheme
        """
        with self.assertRaises(exc.ConfigurationError):
            ArcGIS(
                username='a',
                password='b',
                referer='http://www.example.com',
                scheme='http'
            )

    def test_geocode(self):
        """
        ArcGIS.geocode
        """
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        """
        ArcGIS.geocode unicode
        """
        self.geocode_run(
            {"query": u("\u6545\u5bab")},
            {"latitude": 39.916, "longitude": 116.390},
        )

    def test_empty_response(self):
        self.geocode_run(
            {"query": "dksahdksahdjksahdoufydshf"},
            {},
            expect_failure=True
        )

    def test_geocode_with_out_fields_string(self):
        """
        ArcGIS.geocode with outFields string
        """
        result = self.geocode_run(
            {"query": "Trafalgar Square, London",
             "out_fields": "Country"},
            {}
        )
        self.assertDictEqual(result.raw['attributes'],
                             {'Country': 'GBR'})

    def test_geocode_with_out_fields_list(self):
        """
        ArcGIS.geocode with outFields list
        """
        result = self.geocode_run(
            {"query": "Trafalgar Square, London",
             "out_fields": ["City", "Type"]},
            {}
        )
        self.assertDictEqual(result.raw['attributes'],
                             {'City': 'London', 'Type': 'Tourist Attraction'})

    def test_reverse_point(self):
        """
        ArcGIS.reverse using point
        """
        location = self.reverse_run(
            {"query": Point(40.753898, -73.985071)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )
        self.assertIn('New York', location.address)

    def test_reverse_not_exactly_one(self):
        self.reverse_run(
            {"query": Point(40.753898, -73.985071), "exactly_one": False},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    def test_reverse_no_result(self):
        self.reverse_run(
            # North Atlantic Ocean
            {"query": (35.173809, -37.485351)},
            {},
            expect_failure=True
        )

    def test_custom_wkid(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            # Custom wkid should be ignored and a warning should be issued.
            location = self.reverse_run(
                {"query": Point(40.753898, -73.985071), "wkid": 2000},
                {"latitude": 40.75376406311989,
                 "longitude": -73.98489005863667},
            )
            self.assertIn('New York', location.address)
            self.assertEqual(1, len(w))


@unittest.skipUnless(
    (env.get('ARCGIS_USERNAME') is not None
     or env.get('ARCGIS_PASSWORD') is not None
     or env.get('ARCGIS_REFERER') is not None),
    "No ARCGIS_USERNAME or ARCGIS_PASSWORD or ARCGIS_REFERER env variable set"
)
class ArcGISAuthenticatedTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = ArcGIS(
            username=env['ARCGIS_USERNAME'],
            password=env['ARCGIS_PASSWORD'],
            referer=env['ARCGIS_REFERER'],
            timeout=3
        )

    def test_basic_address(self):
        """
        ArcGIS.geocode using authentication
        """
        self.geocode_run(
            {"query": "Potsdamer Platz, Berlin, Deutschland"},
            {"latitude": 52.5094982, "longitude": 13.3765983},
        )
