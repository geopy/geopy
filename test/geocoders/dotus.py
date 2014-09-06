
import unittest

from geopy.compat import py3k
from geopy.geocoders import GeocoderDotUS
from test.geocoders.util import GeocoderTestBase, env

@unittest.skipUnless(  # pylint: disable=R0904,C0111
    bool(env.get('GEOCODERDOTUS_USERNAME')) and \
    bool(env.get('GEOCODERDOTUS_PASSWORD')),
    "No GEOCODERDOTUS_USERNAME and GEOCODERDOTUS_PASSWORD env variables set"
)
class GeocoderDotUSTestCase(GeocoderTestBase): # pylint: disable=R0904,C0111

    @classmethod
    def setUpClass(cls):
        cls.geocoder = GeocoderDotUS(
            username=env['GEOCODERDOTUS_USERNAME'],
            password=env['GEOCODERDOTUS_PASSWORD'],
            timeout=3
        )

    def test_dot_us_auth(self):
        """
        GeocoderDotUS Authorization header
        """
        geocoder = GeocoderDotUS(username='username', password='password')

        def _print_call_geocoder(query, timeout, raw):
            """
            We want to abort at call time and just get the request object.
            """
            raise Exception(query)

        geocoder._call_geocoder = _print_call_geocoder
        exc_raised = False
        try:
            geocoder.geocode("1 5th Ave NYC")
        except Exception as err:
            exc_raised = True
            request = err.message if not py3k else err.args[0]
            self.assertEqual(
                request.get_header('Authorization'),
                'Basic dXNlcm5hbWU6cGFzc3dvcmQ='
            )
        self.assertTrue(exc_raised)

    def test_geocode(self):
        """
        GeocoderDotUS.geocode
        """
        self.geocode_run(
            {"query": u"435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        """
        GeocoderDotUS.geocode unicode
        """
        self.geocode_run(
            {"query": u"\u6545\u5bab"},
            {"latitude": 39.916, "longitude": 116.390},
        )
