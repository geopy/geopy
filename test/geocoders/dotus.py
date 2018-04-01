
import unittest
from mock import patch

from geopy.compat import u
from geopy.compat import py3k
from geopy.geocoders import GeocoderDotUS
from test.geocoders.util import GeocoderTestBase, env


class GeocoderDotUSTestCaseUnitTest(GeocoderTestBase):

    def test_user_agent_custom(self):
        geocoder = GeocoderDotUS(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_dot_us_auth(self):
        """
        GeocoderDotUS Authorization header
        """
        geocoder = GeocoderDotUS(username='username', password='password')
        with patch.object(geocoder, '_call_geocoder',
                          side_effect=NotImplementedError()) as mock_call_geocoder:
            with self.assertRaises(NotImplementedError):
                geocoder.geocode("1 5th Ave NYC")
            args, kwargs = mock_call_geocoder.call_args
            request = args[0]
            self.assertEqual(
                request.get_header('Authorization'),
                'Basic dXNlcm5hbWU6cGFzc3dvcmQ='
            )

    def test_get_headers(self):
        geocoder = GeocoderDotUS()
        self.assertDictEqual({}, geocoder._get_headers())

        username = 'testuser'
        password = 'testpassword'
        # echo -n testuser:testpassword | base64
        b64 = 'dGVzdHVzZXI6dGVzdHBhc3N3b3Jk'
        geocoder = GeocoderDotUS(username=username, password=password)
        self.assertDictEqual({'Authorization': 'Basic %s' % b64},
                             geocoder._get_headers())


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

    def test_geocode(self):
        """
        GeocoderDotUS.geocode
        """
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        """
        GeocoderDotUS.geocode unicode
        """
        self.geocode_run(
            {"query": u("\u6545\u5bab")},
            {"latitude": 39.916, "longitude": 116.390},
        )
