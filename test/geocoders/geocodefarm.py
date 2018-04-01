
import unittest
import types

from geopy import exc
from geopy.point import Point
from geopy.geocoders import GeocodeFarm
from test.geocoders.util import GeocoderTestBase, env


class GeocodeFarmTestCase(GeocoderTestBase): # pylint: disable=R0904,C0111

    @classmethod
    def setUpClass(cls):
        cls.delta = 0.04
        cls.geocoder = GeocodeFarm(
            api_key=env.get('GEOCODEFARM_KEY'), # None api_key will use free tier on GeocodeFarm
            timeout=10,
        )

    def setUp(self):
        # Store the original _call_geocoder in case we replace it with a mock
        self._original_call_geocoder = self.geocoder._call_geocoder

    def tearDown(self):
        # Restore the original _call_geocoder in case we replaced it with a mock
        self.geocoder._call_geocoder = self._original_call_geocoder

    def test_user_agent_custom(self):
        geocoder = GeocodeFarm(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_geocode(self):
        """
        GeocodeFarm.geocode
        """
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_reverse_string(self):
        """
        GeocodeFarm.reverse string
        """
        self.reverse_run(
            {"query": "40.75376406311989,-73.98489005863667"},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    def test_reverse_point(self):
        """
        GeocodeFarm.reverse Point
        """
        self.reverse_run(
            {"query": Point(40.75376406311989, -73.98489005863667)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    def test_authentication_failure(self):
        """
        GeocodeFarm authentication failure
        """
        self.geocoder = GeocodeFarm(api_key="invalid")
        try:
            with self.assertRaises(exc.GeocoderAuthenticationFailure):
                address = '435 north michigan ave, chicago il 60611'
                self.geocoder.geocode(address)
        except exc.GeocoderTimedOut:
            raise unittest.SkipTest("GeocodeFarm timed out")

    def test_quota_exceeded(self):
        """
        GeocodeFarm quota exceeded
        """

        def mock_call_geocoder(*args, **kwargs):
            """
            Mock API call to return bad response.
            """
            return {
                "geocoding_results": {
                    "STATUS": {
                        "access": "OVER_QUERY_LIMIT",
                        "status": "FAILED, ACCESS_DENIED"
                    }
                }
            }
        self.geocoder._call_geocoder = types.MethodType(
            mock_call_geocoder,
            self.geocoder
        )

        with self.assertRaises(exc.GeocoderQuotaExceeded):
            self.geocoder.geocode('435 north michigan ave, chicago il 60611')

    def test_unhandled_api_error(self):
        """
        GeocodeFarm unhandled error
        """

        def mock_call_geocoder(*args, **kwargs):
            """
            Mock API call to return bad response.
            """
            return {
                "geocoding_results": {
                    "STATUS": {
                        "access": "BILL_PAST_DUE",
                        "status": "FAILED, ACCESS_DENIED"
                    }
                }
            }
        self.geocoder._call_geocoder = types.MethodType(
            mock_call_geocoder,
            self.geocoder
        )

        with self.assertRaises(exc.GeocoderServiceError):
            self.geocoder.geocode('435 north michigan ave, chicago il 60611')
