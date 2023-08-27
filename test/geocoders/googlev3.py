import base64
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import pytest

from geopy import exc
from geopy.geocoders import GoogleV3
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env

try:
    import pytz
    pytz_available = True
except ImportError:
    pytz_available = False


class TestGoogleV3(BaseTestGeocoder):
    new_york_point = Point(40.75376406311989, -73.98489005863667)

    @classmethod
    def make_geocoder(cls, **kwargs):
        return GoogleV3(api_key=env['GOOGLE_KEY'], **kwargs)

    async def test_user_agent_custom(self):
        geocoder = GoogleV3(
            api_key='mock',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    async def test_configuration_error(self):
        with pytest.raises(exc.ConfigurationError):
            GoogleV3(api_key='mock', client_id='a')
        with pytest.raises(exc.ConfigurationError):
            GoogleV3(api_key='mock', secret_key='a')

    async def test_error_with_no_api_key(self):
        with pytest.raises(exc.ConfigurationError):
            GoogleV3()

    async def test_no_error_with_no_api_key_but_using_premier(self):
        GoogleV3(client_id='client_id', secret_key='secret_key')

    async def test_check_status(self):
        def make_error(status, error_message=None):
            return {
                "status": status,
                **({"error_message": error_message} if error_message else {}),
            }

        assert self.geocoder._check_status(make_error("ZERO_RESULTS")) is None
        with pytest.raises(exc.GeocoderQuotaExceeded):
            self.geocoder._check_status(make_error("OVER_QUERY_LIMIT"))
        with pytest.raises(exc.GeocoderQueryError):
            self.geocoder._check_status(make_error("REQUEST_DENIED"))
        with pytest.raises(exc.GeocoderQueryError):
            self.geocoder._check_status(make_error("INVALID_REQUEST"))
        with pytest.raises(exc.GeocoderServiceError):
            self.geocoder._check_status(make_error("_"))

    async def test_get_signed_url(self):
        geocoder = GoogleV3(
            api_key='mock',
            client_id='my_client_id',
            secret_key=base64.urlsafe_b64encode(b'my_secret_key')
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

    async def test_get_signed_url_with_channel(self):
        geocoder = GoogleV3(
            api_key='mock',
            client_id='my_client_id',
            secret_key=base64.urlsafe_b64encode(b'my_secret_key'),
            channel='my_channel'
        )

        signed_url = geocoder._get_signed_url({'address': '1 5th Ave New York, NY'})
        params = parse_qs(urlparse(signed_url).query)

        assert 'channel' in params
        assert 'signature' in params
        assert 'client' in params

    async def test_format_components_param(self):
        f = self.geocoder._format_components_param
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

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    async def test_geocode_with_conflicting_components(self):
        await self.geocode_run(
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

        await self.geocode_run(
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

    async def test_components(self):
        await self.geocode_run(
            {
                "query": "santa cruz",
                "components": {
                    "country": "ES"
                }
            },
            {"latitude": 28.4636296, "longitude": -16.2518467},
        )

        await self.geocode_run(
            {
                "query": "santa cruz",
                "components": [
                    ('country', 'ES')
                ]
            },
            {"latitude": 28.4636296, "longitude": -16.2518467},
        )

    async def test_components_without_query(self):
        await self.geocode_run(
            {
                "components": {"city": "Paris", "country": "FR"},
            },
            {"latitude": 46.227638, "longitude": 2.213749},
        )

        await self.geocode_run(
            {
                "components": [("city", "Paris"), ("country", "FR")],
            },
            {"latitude": 46.227638, "longitude": 2.213749},
        )

    async def test_reverse(self):
        await self.reverse_run(
            {"query": self.new_york_point},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    async def test_zero_results(self):
        with pytest.raises(exc.GeocoderQueryError):
            await self.geocode_run(
                {"query": ''},
                {},
                expect_failure=True,
            )

    @pytest.mark.skipif("not pytz_available")
    async def test_timezone_datetime(self):
        await self.reverse_timezone_run(
            {"query": self.new_york_point,
             "at_time": datetime.utcfromtimestamp(0)},
            pytz.timezone("America/New_York"),
        )

    @pytest.mark.skipif("not pytz_available")
    async def test_timezone_at_time_normalization(self):
        utc_naive_dt = datetime(2010, 1, 1, 0, 0, 0)
        utc_timestamp = 1262304000
        assert (
            utc_timestamp == self.geocoder._normalize_timezone_at_time(utc_naive_dt)
        )

        assert (
            utc_timestamp < self.geocoder._normalize_timezone_at_time(None)
        )

        tz = pytz.timezone("Etc/GMT-2")
        local_aware_dt = tz.localize(datetime(2010, 1, 1, 2, 0, 0))
        assert (
            utc_timestamp == self.geocoder._normalize_timezone_at_time(local_aware_dt)
        )

    @pytest.mark.skipif("not pytz_available")
    async def test_timezone_integer_raises(self):
        # In geopy 1.x `at_time` could be an integer -- a unix timestamp.
        # This is an error since geopy 2.0.
        with pytest.raises(exc.GeocoderQueryError):
            await self.reverse_timezone_run(
                {"query": self.new_york_point, "at_time": 0},
                pytz.timezone("America/New_York"),
            )

    @pytest.mark.skipif("not pytz_available")
    async def test_timezone_no_date(self):
        await self.reverse_timezone_run(
            {"query": self.new_york_point},
            pytz.timezone("America/New_York"),
        )

    @pytest.mark.skipif("not pytz_available")
    async def test_timezone_invalid_at_time(self):
        with pytest.raises(exc.GeocoderQueryError):
            self.geocoder.reverse_timezone(self.new_york_point, at_time="eek")

    @pytest.mark.skipif("not pytz_available")
    async def test_reverse_timezone_unknown(self):
        await self.reverse_timezone_run(
            # Google doesn't return a timezone for Antarctica.
            {"query": "89.0, 1.0"},
            None,
        )

    async def test_geocode_bounds(self):
        await self.geocode_run(
            {"query": "Washington", "bounds": [[36.47, -84.72], [43.39, -65.90]]},
            {"latitude": 38.9071923, "longitude": -77.0368707, "delta": 8}
        )

    async def test_geocode_bounds_invalid(self):
        with pytest.raises(exc.GeocoderQueryError):
            await self.geocode_run(
                {"query": "221b Baker St", "bounds": [50, -2, 55]},
                {"latitude": 51.52, "longitude": -0.15},
            )

    async def test_geocode_place_id_invalid(self):
        await self.geocode_run(
            {"place_id": "ChIJOcfP0Iq2j4ARDrXUa7ZWs34"},
            {"latitude": 37.22, "longitude": -122.05}
        )

    async def test_geocode_place_id_not_invalid(self):
        with pytest.raises(exc.GeocoderQueryError):
            await self.geocode_run(
                {"place_id": "xxxxx"},
                {},
                expect_failure=True,
            )

    async def test_place_id_zero_result(self):
        with pytest.raises(exc.GeocoderQueryError):
            await self.geocode_run(
                {"place_id": ""},
                {},
                expect_failure=True,
            )

    async def test_geocode_place_id_with_query(self):
        with pytest.raises(ValueError):
            await self.geocode_run(
                {"place_id": "ChIJOcfP0Iq2j4ARDrXUa7ZWs34",
                 "query": "silicon valley"},
                {}
            )

    async def test_geocode_place_id_with_bounds(self):
        with pytest.raises(ValueError):
            await self.geocode_run(
                {"place_id": "ChIJOcfP0Iq2j4ARDrXUa7ZWs34",
                 "bounds": [50, -2, 55, 2]},
                {}
            )

    async def test_geocode_place_id_with_query_and_bounds(self):
        with pytest.raises(ValueError):
            await self.geocode_run(
                {"place_id": "ChIJOcfP0Iq2j4ARDrXUa7ZWs34",
                 "query": "silicon valley",
                 "bounds": [50, -2, 55, 2]},
                {}
            )
