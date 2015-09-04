
import unittest

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


@unittest.skipUnless(  # pylint: disable=R0904,C0111
    bool(env.get('ARCGIS_USERNAME')),
    "No ARCGIS_USERNAME env variable set"
)
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

    def test_reverse_point(self):
        """
        ArcGIS.reverse using point
        """
        self.reverse_run(
            {"query": Point(40.753898, -73.985071)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )


@unittest.skipUnless(  # pylint: disable=R0904,C0111
    env.get('ARCGIS_USERNAME') is not None \
    or env.get('ARCGIS_PASSWORD') is not None\
    or env.get('ARCGIS_REFERER') is not None,
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
