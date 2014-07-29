
import unittest
import types

from geopy import exc
from geopy.geocoders import GeocodeFarm
from test.geocoders.util import GeocoderTestBase, CommonTestMixin, env


@unittest.skipUnless( # pylint: disable=R0904,C0111
    env['GEOCODEFARM_KEY'] is not None,
    "GEOCODEFARM_KEY env variable not set"
)
class GeocodeFarmTestCase(GeocoderTestBase, CommonTestMixin): # pylint: disable=R0904,C0111

    @classmethod
    def setUpClass(cls):
        cls.delta = 0.04
        cls.geocoder = GeocodeFarm(
            api_key=env['GEOCODEFARM_KEY'],
            format_string="%s US"
        )

    def test_reverse(self):
        """
        GeocodeFarm.reverse
        """
        self.reverse_run(
            {"query": u"1065 6th Ave, New York, NY 10018, United States"},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    def test_authentication_failure(self):
        """
        GeocodeFarm authentication failure
        """
        self.geocoder = GeocodeFarm(api_key="invalid")
        with self.assertRaises(exc.GeocoderAuthenticationFailure):
            address = '435 north michigan ave, chicago il 60611'
            self.geocoder.geocode(address)

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
            self.geocoder.geocode(u'435 north michigan ave, chicago il 60611')

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
            self.geocoder.geocode(u'435 north michigan ave, chicago il 60611')
