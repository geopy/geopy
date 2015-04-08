import base64
from datetime import datetime
from pytz import timezone

from geopy import exc
from geopy.compat import u
from geopy.point import Point
from geopy.geocoders import GoogleV3
from test.geocoders.util import GeocoderTestBase


class GoogleV3TestCase(GeocoderTestBase): # pylint: disable=R0904,C0111

    @classmethod
    def setUpClass(cls):
        cls.geocoder = GoogleV3()
        cls.new_york_point = Point(40.75376406311989, -73.98489005863667)
        cls.america_new_york = timezone("America/New_York")

    def test_user_agent_custom(self):
        geocoder = GoogleV3(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_configuration_error(self):
        """
        GoogleV3 raises configuration errors on invalid auth params
        """
        with self.assertRaises(exc.ConfigurationError):
            GoogleV3(client_id='a')
        with self.assertRaises(exc.ConfigurationError):
            GoogleV3(secret_key='a')

    def test_check_status(self):
        """
        GoogleV3 raises correctly on Google-specific API status flags
        """
        self.assertEqual(self.geocoder._check_status("ZERO_RESULTS"), None)
        with self.assertRaises(exc.GeocoderQuotaExceeded):
            self.geocoder._check_status("OVER_QUERY_LIMIT")
        with self.assertRaises(exc.GeocoderQueryError):
            self.geocoder._check_status("REQUEST_DENIED")
        with self.assertRaises(exc.GeocoderQueryError):
            self.geocoder._check_status("INVALID_REQUEST")
        with self.assertRaises(exc.GeocoderQueryError):
            self.geocoder._check_status("_")

    def test_get_signed_url(self):
        """
        GoogleV3._get_signed_url
        """
        geocoder = GoogleV3(
            client_id='my_client_id',
            secret_key=base64.urlsafe_b64encode('my_secret_key'.encode('utf8'))
        )
        self.assertTrue(geocoder.premier)
        # the two possible URLs handle both possible orders of the request
        # params; because it's unordered, either is possible, and each has
        # its own hash
        self.assertTrue(
            geocoder._get_signed_url(
                {'address': '1 5th Ave New York, NY'}
            ) in (
                "https://maps.googleapis.com/maps/api/geocode/json?"
                "address=1+5th+Ave+New+York%2C+NY&client=my_client_id&"
                "signature=Z_1zMBa3Xu0W4VmQfaBR8OQMnDM=",
                "https://maps.googleapis.com/maps/api/geocode/json?"
                "client=my_client_id&address=1+5th+Ave+New+York%2C+NY&"
                "signature=D3PL0cZJrJYfveGSNoGqrrMsz0M="
            )
        )

    def test_format_components_param(self):
        """
        GoogleV3._format_components_param
        """
        f = GoogleV3._format_components_param
        self.assertEqual(f({}), '')
        self.assertEqual(f({'country': 'FR'}), 'country:FR')
        output = f({'administrative_area': 'CA', 'country': 'FR'})
        # the order the dict is iterated over is not important
        self.assertTrue(
            output in (
                'administrative_area:CA|country:FR',
                'country:FR|administrative_area:CA'
            ), output
        )

        with self.assertRaises(AttributeError):
            f(None)

        with self.assertRaises(AttributeError):
            f([])

        with self.assertRaises(AttributeError):
            f('administrative_area:CA|country:FR')

    def test_geocode(self):
        """
        GoogleV3.geocode
        """
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        """
        GoogleV3.geocode unicode
        """
        self.geocode_run(
            {"query": u("\u6545\u5bab")},
            {"latitude": 39.916, "longitude": 116.390},
        )

    def test_geocode_components(self):
        """
        GoogleV3.geocode returns None on conflicting components
        """
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

    def test_components(self):
        """
        GoogleV3.geocode with components
        """
        self.geocode_run(
            {
                "query": "santa cruz",
                "components": {
                    "country": "ES"
                }
            },
            {"latitude": 28.4636296, "longitude": -16.2518467},
        )

    def test_reverse_string(self):
        """
        GoogleV3.reverse string
        """
        self.reverse_run(
            {"query": "40.75376406311989, -73.98489005863667"},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    def test_reverse_point(self):
        """
        GoogleV3.reverse Point
        """
        self.reverse_run(
            {"query": self.new_york_point},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    def test_zero_results(self):
        """
        GoogleV3.geocode returns None for no result
        """
        result = self._make_request(self.geocoder.geocode, '')
        self.assertIsNone(result)

    def test_timezone_datetime(self):
        """
        GoogleV3.timezone returns pytz object from datetime
        """
        tz = self._make_request(
            self.geocoder.timezone,
            self.new_york_point,
            datetime.utcfromtimestamp(0)
        )
        self.assertEqual(tz, self.america_new_york)

    def test_timezone_integer(self):
        """
        GoogleV3.timezone returns pytz object from epoch integer
        """
        tz = self._make_request(
            self.geocoder.timezone,
            self.new_york_point,
            0
        )
        self.assertEqual(tz, self.america_new_york)

    def test_timezone_no_date(self):
        """
        GoogleV3.timezone defaults `at_time`
        """
        tz = self._make_request(
            self.geocoder.timezone,
            self.new_york_point,
        )
        self.assertEqual(tz, self.america_new_york)

    def test_timezone_invalid_at_time(self):
        """
        GoogleV3.timezone invalid `at_time`
        """
        with self.assertRaises(exc.GeocoderQueryError):
            self.geocoder.timezone(self.new_york_point, "eek")

    def test_geocode_bounds(self):
        """
        GoogleV3.geocode check bounds restriction
        """
        self.geocode_run(
            {"query": "221b Baker St", "bounds": [50, -2, 55, 2]},
            {"latitude": 51.52, "longitude": -0.15},
        )

    def test_geocode_bounds_invalid(self):
        """
        GoogleV3.geocode bounds must be 4-length iterable
        """
        with self.assertRaises(exc.GeocoderQueryError):
            self.geocode_run(
                {"query": "221b Baker St", "bounds": [50, -2, 55]},
                {"latitude": 51.52, "longitude": -0.15},
            )
