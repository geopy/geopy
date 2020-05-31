import pytest
from mock import patch

from geopy import exc
from geopy.geocoders import GeocodeFarm
from geopy.point import Point
from test.geocoders.util import GeocoderTestBase, env


@pytest.mark.xfail(
    env.get('GEOCODEFARM_SKIP'),
    reason=(
        "geocodefarm service is unstable at times"
    )
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
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    def test_geocode(self):
        location = self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )
        assert "chicago" in location.address.lower()

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
            skiptest_on_failure=True,  # sometimes the result is empty
        )
        assert "new york" in location.address.lower()

    def test_authentication_failure(self):
        self.geocoder = GeocodeFarm(api_key="invalid")
        with pytest.raises(exc.GeocoderAuthenticationFailure):
            self.geocode_run(
                {"query": '435 north michigan ave, chicago il 60611'},
                {},
                expect_failure=True,
            )

    def test_quota_exceeded(self):

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
                pytest.raises(exc.GeocoderQuotaExceeded):
            self.geocoder.geocode('435 north michigan ave, chicago il 60611')

    def test_no_results(self):
        self.geocode_run(
            {"query": "gibberish kdjhsakdjh skjdhsakjdh"},
            {},
            expect_failure=True
        )

    def test_unhandled_api_error(self):

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
                pytest.raises(exc.GeocoderServiceError):
            self.geocoder.geocode('435 north michigan ave, chicago il 60611')
