from mock import patch
import unittest

from geopy import exc
from geopy.geocoders import GeocodeFarm
from geopy.point import Point
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(
    not env.get('GEOCODEFARM_SKIP'),
    "GEOCODEFARM_SKIP env variable is set"
)
class GeocodeFarmTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.delta = 0.04
        cls.geocoder = GeocodeFarm(
            # None api_key will use free tier on GeocodeFarm.
            api_key=env.get('GEOCODEFARM_KEY'),
            timeout=10,
        )

    def test_user_agent_custom(self):
        geocoder = GeocodeFarm(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_geocode(self):
        """
        GeocodeFarm.geocode
        """
        location = self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )
        self.assertIn("chicago", location.address.lower())

    def test_location_address(self):
        self.geocode_run(
            {"query": "moscow"},
            {"address": "Moscow, Russia",
             "latitude": 55.7558913503453, "longitude": 37.6172961632184}
        )

    def test_reverse(self):
        location = self.reverse_run(
            {"query": Point(40.75376406311989, -73.98489005863667)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )
        self.assertIn("new york", location.address.lower())

    def test_authentication_failure(self):
        """
        GeocodeFarm authentication failure
        """
        self.geocoder = GeocodeFarm(api_key="invalid")
        with self.assertRaises(exc.GeocoderAuthenticationFailure):
            self.geocode_run(
                {"query": '435 north michigan ave, chicago il 60611'},
                {},
                expect_failure=True,
            )

    def test_quota_exceeded(self):
        """
        GeocodeFarm quota exceeded
        """

        def mock_call_geocoder(*args, **kwargs):
            return {
                "geocoding_results": {
                    "STATUS": {
                        "access": "OVER_QUERY_LIMIT",
                        "status": "FAILED, ACCESS_DENIED"
                    }
                }
            }

        with patch.object(self.geocoder, '_call_geocoder', mock_call_geocoder), \
                self.assertRaises(exc.GeocoderQuotaExceeded):
            self.geocoder.geocode('435 north michigan ave, chicago il 60611')

    def test_no_results(self):
        self.geocode_run(
            {"query": "gibberish kdjhsakdjh skjdhsakjdh"},
            {},
            expect_failure=True
        )

    def test_unhandled_api_error(self):
        """
        GeocodeFarm unhandled error
        """

        def mock_call_geocoder(*args, **kwargs):
            return {
                "geocoding_results": {
                    "STATUS": {
                        "access": "BILL_PAST_DUE",
                        "status": "FAILED, ACCESS_DENIED"
                    }
                }
            }

        with patch.object(self.geocoder, '_call_geocoder', mock_call_geocoder), \
                self.assertRaises(exc.GeocoderServiceError):
            self.geocoder.geocode('435 north michigan ave, chicago il 60611')
