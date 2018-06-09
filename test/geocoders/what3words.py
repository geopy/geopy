import unittest
from mock import patch

import geopy.geocoders
import geopy.exc
from geopy.compat import u
from geopy.geocoders import What3Words
from test.geocoders.util import GeocoderTestBase, env


class What3WordsTestCaseUnitTest(GeocoderTestBase):
    dummy_api_key = 'DUMMYKEY1234'

    def test_user_agent_custom(self):
        geocoder = What3Words(
            api_key=self.dummy_api_key,
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_http_scheme_is_disallowed(self):
        with self.assertRaises(geopy.exc.ConfigurationError):
            What3Words(
                api_key=self.dummy_api_key,
                scheme='http',
            )

    @patch.object(geopy.geocoders.options, 'default_scheme', 'http')
    def test_default_scheme_is_ignored(self):
        geocoder = What3Words(api_key=self.dummy_api_key)
        self.assertEqual(geocoder.scheme, 'https')
        geocoder = What3Words(api_key=self.dummy_api_key, scheme=None)
        self.assertEqual(geocoder.scheme, 'https')


@unittest.skipUnless(
    bool(env.get('WHAT3WORDS_KEY')),
    "No WHAT3WORDS_KEY env variable set"
)
class What3WordsTestCase(GeocoderTestBase):
    @classmethod
    def setUpClass(cls):
        cls.geocoder = What3Words(
            env['WHAT3WORDS_KEY'],
            scheme='https',
            timeout=3

        )
        cls.delta = 0.7

    def test_geocode(self):
        self.geocode_run(
            {"query": u("piped.gains.jangle")},
            {"latitude": 53.037611, "longitude": 11.565012},
        )

    def test_reverse(self):
        """
        What3Words.reverse - '3 Words'
        """
        self.reverse_run(
            {"query": "53.037611,11.565012", "lang": 'DE'},
            {"address": 'fortschrittliche.voll.schnitt'},
        )

    def test_unicode_query(self):
        """
        What3Words.geocode - '3 Words' unicode
        """
        self.geocode_run(
            {
                "query": u(
                    "\u0070\u0069\u0070\u0065\u0064\u002e\u0067"
                    "\u0061\u0069\u006e\u0073\u002e\u006a\u0061"
                    "\u006e\u0067\u006c\u0065"
                )
            },
            {"latitude": 53.037611, "longitude": 11.565012},
        )

    def test_empty_response(self):
        with self.assertRaises(geopy.exc.GeocoderQueryError):
            self.geocode_run(
                {"query": "definitely.not.existingiswearrrr"},
                {},
                expect_failure=True
            )

    def test_not_exactly_one(self):
        self.geocode_run(
            {"query": "piped.gains.jangle", "exactly_one": False},
            {"latitude": 53.037611, "longitude": 11.565012},
        )
        self.reverse_run(
            {"query": (53.037611, 11.565012), "exactly_one": False},
            {"address": "piped.gains.jangle"},
        )

    def test_result_language(self):
        """
        What3Words.geocode result language
        """
        self.geocode_run(
            {"query": "piped.gains.jangle", "lang": 'DE'},
            {"address": 'fortschrittliche.voll.schnitt'},
        )

    def test_check_query(self):
        result_check_threeword_query = self.geocoder._check_query(
            u(
                "\u0066\u0061\u0068\u0072\u0070\u0072"
                "\u0065\u0069\u0073\u002e\u006c\u00fc"
                "\u0067\u006e\u0065\u0072\u002e\u006b"
                "\u0075\u0074\u0073\u0063\u0068\u0065"
            )
        )

        self.assertTrue(result_check_threeword_query)
