import base64
import unittest
import warnings
from datetime import datetime

import pytest
from pytz import timezone

from geopy import exc
from geopy.compat import parse_qs, u, urlparse
from geopy.geocoders import GoogleV3
from geopy.point import Point
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(
    bool(env['GOOGLE_KEY']),
    "No GOOGLE_KEY env variable set"
)
class GoogleV3TestCase(GeocoderTestBase):
    new_york_point = Point(40.75376406311989, -73.98489005863667)
    america_new_york = timezone("America/New_York")

    @classmethod
    def setUpClass(cls):
        cls.geocoder = GoogleV3(api_key=env.get('GOOGLE_KEY'))

    def reverse_timezone_run(self, payload, expected):
        timezone = self._make_request(self.geocoder.reverse_timezone, **payload)
        if expected is None:
            assert timezone is None
        else:
            assert timezone.pytz_timezone == expected

        # `timezone` method is deprecated, but we still support it.
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            if 'query' in payload:
                payload['location'] = payload['query']
                del payload['query']
            pytz_timezone = self._make_request(self.geocoder.timezone, **payload)
            if expected is None:
                assert pytz_timezone is None
            else:
                assert pytz_timezone == expected
            assert 0 < len(w)

        return timezone

    def test_user_agent_custom(self):
        geocoder = GoogleV3(
            api_key='mock',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    def test_configuration_error(self):
        with pytest.raises(exc.ConfigurationError):
            GoogleV3(api_key='mock', client_id='a')
        with pytest.raises(exc.ConfigurationError):
            GoogleV3(api_key='mock', secret_key='a')

    def test_warning_with_no_api_key(self):
        with warnings.catch_warnings(record=True) as w:
            GoogleV3()
        assert len(w) == 1

    def test_no_warning_with_no_api_key_but_using_premier(self):
        with warnings.catch_warnings(record=True) as w:
            GoogleV3(client_id='client_id', secret_key='secret_key')
        assert len(w) == 0

    def test_check_status(self):
        assert self.geocoder._check_status("ZERO_RESULTS") is None
        with pytest.raises(exc.GeocoderQuotaExceeded):
            self.geocoder._check_status("OVER_QUERY_LIMIT")
        with pytest.raises(exc.GeocoderQueryError):
            self.geocoder._check_status("REQUEST_DENIED")
        with pytest.raises(exc.GeocoderQueryError):
            self.geocoder._check_status("INVALID_REQUEST")
        with pytest.raises(exc.GeocoderQueryError):
            self.geocoder._check_status("_")

    def test_get_signed_url(self):
        geocoder = GoogleV3(
            api_key='mock',
            client_id='my_client_id',
            secret_key=base64.urlsafe_b64encode('my_secret_key'.encode('utf8'))
        )
        assert geocoder.premier
        # the two possible URLs handle both possible orders of the request
        # params; because it's unordered, either is possible, and each has
        # its own hash
        assert geocoder._get_signed_url(
            {'address': '1 5th Ave New York, NY'}
        ) in (
            "https://maps.googleapis.com/maps/api/geocode/json?"
            "address=1+5th+Ave+New+York%2C+NY&client=my_client_id&"
            "signature=Z_1zMBa3Xu0W4VmQfaBR8OQMnDM=",
            "https://maps.googleapis.com/maps/api/geocode/json?"
            "client=my_client_id&address=1+5th+Ave+New+York%2C+NY&"
            "signature=D3PL0cZJrJYfveGSNoGqrrMsz0M="
        )

    def test_get_signed_url_with_channel(self):
        geocoder = GoogleV3(
            api_key='mock',
            client_id='my_client_id',
            secret_key=base64.urlsafe_b64encode('my_secret_key'.encode('utf8')),
            channel='my_channel'
        )

        signed_url = geocoder._get_signed_url({'address': '1 5th Ave New York, NY'})
        params = parse_qs(urlparse(signed_url).query)

        assert 'channel' in params
        assert 'signature' in params
        assert 'client' in params

    def test_format_components_param(self):
        f = GoogleV3._format_components_param
        assert f({}) == ''
        assert f([]) == ''

        assert f({'country': 'FR'}) == 'country:FR'
        output = f({'administrative_area': 'CA', 'country': 'FR'})
        # the order the dict is iterated over is not important
        assert output in (
            'administrative_area:CA|country:FR',
            'country:FR|administrative_area:CA'
        ), output

        assert f([('country', 'FR')]) == 'country:FR'
        output = f([
            ('administrative_area', 'CA'),
            ('administrative_area', 'Los Angeles'),
            ('country', 'US')
        ])
        assert (
            output ==
            'administrative_area:CA|administrative_area:Los Angeles|country:US'
        )

        with pytest.raises(ValueError):
            f(None)

        with pytest.raises(ValueError):
            f('administrative_area:CA|country:FR')

    def test_geocode(self):
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        self.geocode_run(
            {"query": u("\u6545\u5bab")},
            {"latitude": 39.916, "longitude": 116.390},
        )

    def test_geocode_with_conflicting_components(self):
        self.geocode_run(
            {
                "query": "santa cruz",
                "components": {
                    "administrative_area": "CA",
                    "country": "FR"
                }
            },
            {},
            expect_failure=True
        )

        self.geocode_run(
            {
                "query": "santa cruz",
                "components": [
                    ('administrative_area', 'CA'),
                    ('country', 'FR')
                ]
            },
            {},
            expect_failure=True
        )

    def test_components(self):
        self.geocode_run(
            {
                "query": "santa cruz",
                "components": {
                    "country": "ES"
                }
            },
            {"latitude": 28.4636296, "longitude": -16.2518467},
        )

        self.geocode_run(
            {
                "query": "santa cruz",
                "components": [
                    ('country', 'ES')
                ]
            },
            {"latitude": 28.4636296, "longitude": -16.2518467},
        )

    def test_components_without_query(self):
        self.geocode_run(
            {
                "components": {"city": "Paris", "country": "FR"},
            },
            {"latitude": 46.227638, "longitude": 2.213749},
        )

        self.geocode_run(
            {
                "components": [("city", "Paris"), ("country", "FR")],
            },
            {"latitude": 46.227638, "longitude": 2.213749},
        )

    def test_reverse(self):
        self.reverse_run(
            {"query": self.new_york_point, "exactly_one": True},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    def test_zero_results(self):
        with pytest.raises(exc.GeocoderQueryError):
            self.geocode_run(
                {"query": ''},
                {},
                expect_failure=True,
            )

    def test_timezone_datetime(self):
        self.reverse_timezone_run(
            {"query": self.new_york_point,
             "at_time": datetime.utcfromtimestamp(0)},
            self.america_new_york,
        )

    def test_timezone_at_time_normalization(self):
        utc_naive_dt = datetime(2010, 1, 1, 0, 0, 0)
        utc_timestamp = 1262304000
        assert (
            utc_timestamp == self.geocoder._normalize_timezone_at_time(utc_naive_dt)
        )

        assert (
            utc_timestamp < self.geocoder._normalize_timezone_at_time(None)
        )

        tz = timezone("Etc/GMT-2")
        local_aware_dt = tz.localize(datetime(2010, 1, 1, 2, 0, 0))
        assert(
            utc_timestamp == self.geocoder._normalize_timezone_at_time(local_aware_dt)
        )

    def test_timezone_integer(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            self.reverse_timezone_run(
                {"query": self.new_york_point, "at_time": 0},
                self.america_new_york,
            )
            # at_time as number should issue a warning
            assert 0 < len(w)

    def test_timezone_no_date(self):
        self.reverse_timezone_run(
            {"query": self.new_york_point},
            self.america_new_york,
        )

    def test_timezone_invalid_at_time(self):
        with pytest.raises(exc.GeocoderQueryError):
            self.geocoder.reverse_timezone(self.new_york_point, "eek")

    def test_reverse_timezone_unknown(self):
        self.reverse_timezone_run(
            # Google doesn't return a timezone for Antarctica.
            {"query": "89.0, 1.0"},
            None,
        )

    def test_geocode_bounds(self):
        self.geocode_run(
            {"query": "221b Baker St", "bounds": [[50, -2], [55, 2]]},
            {"latitude": 51.52, "longitude": -0.15},
        )

    def test_geocode_bounds_deprecated(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            self.geocode_run(
                {"query": "221b Baker St", "bounds": [50, -2, 55, 2]},
                {"latitude": 51.52, "longitude": -0.15},
            )
            assert 1 == len(w)

    def test_geocode_bounds_invalid(self):
        with pytest.raises(exc.GeocoderQueryError):
            self.geocode_run(
                {"query": "221b Baker St", "bounds": [50, -2, 55]},
                {"latitude": 51.52, "longitude": -0.15},
            )

    def test_geocode_place_id_invalid(self):
        self.geocode_run(
            {"place_id": "ChIJOcfP0Iq2j4ARDrXUa7ZWs34"},
            {"latitude": 37.22, "longitude": -122.05}
        )

    def test_geocode_place_id_not_invalid(self):
        with pytest.raises(exc.GeocoderQueryError):
            self.geocode_run(
                {"place_id": "xxxxx"},
                {},
                expect_failure=True,
            )

    def test_place_id_zero_result(self):
        with pytest.raises(exc.GeocoderQueryError):
            self.geocode_run(
                {"place_id": ""},
                {},
                expect_failure=True,
            )

    def test_geocode_place_id_with_query(self):
        with pytest.raises(ValueError):
            self.geocode_run(
                {"place_id": "ChIJOcfP0Iq2j4ARDrXUa7ZWs34",
                 "query": "silicon valley"},
                {}
            )

    def test_geocode_place_id_with_bounds(self):
        with pytest.raises(ValueError):
            self.geocode_run(
                {"place_id": "ChIJOcfP0Iq2j4ARDrXUa7ZWs34",
                 "bounds": [50, -2, 55, 2]},
                {}
            )

    def test_geocode_place_id_with_query_and_bounds(self):
        with pytest.raises(ValueError):
            self.geocode_run(
                {"place_id": "ChIJOcfP0Iq2j4ARDrXUa7ZWs34",
                 "query": "silicon valley",
                 "bounds": [50, -2, 55, 2]},
                {}
            )
