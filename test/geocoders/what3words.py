import unittest

from geopy.geocoders import What3Words
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(bool(env.get('WHAT3WORDS_KEY')),
                     "No WHAT3WORDS_KEY env variable set"
)
class What3WordsTestCase(GeocoderTestBase):
    @classmethod
    def setUpClass(cls):
        cls.geocoder = What3Words(
            env['WHAT3WORDS_KEY'],
            scheme='http',
            timeout=3

        )
        cls.delta = 0.7

    def test_geocode(self):
        """
        What3Words.geocode - '3 Words' and 'OneWord'
        """
        self.geocode_run(
            {"query": u"piped.gains.jangle"},
            {"latitude": 53.037611, "longitude": 11.565012},
        )

        self.geocode_run(
            {"query": u"*LibertyTech"},
            {"latitude": 51.512573, "longitude": -0.144879},
        )


    def test_reverse(self):
        """
        What3Words.reverse - '3 Words'
        """
        result_reverse = self._make_request(
            self.geocoder.reverse,
            "53.037611,11.565012",
            lang='DE',

        )
        self.assertEqual(
            result_reverse.address,
            'unwesen.voll.schnitt'
        )


    def test_unicode_query(self):
        """
        What3Words.geocode - '3 Words' unicode
        """
        self.geocode_run(
            {
                "query": (
                    u"\u0070\u0069\u0070\u0065\u0064\u002e\u0067"
                    u"\u0061\u0069\u006e\u0073\u002e\u006a\u0061"
                    u"\u006e\u0067\u006c\u0065"
                )
            },
            {"latitude": 53.037611, "longitude": 11.565012},
        )

        self.geocode_run(
            {
                "query": (
                    u"\u002a\u004c\u0069\u0062\u0065\u0072\u0074"
                    u"\u0079\u0054\u0065\u0063\u0068"
                )
            },
            {"latitude": 51.512573, "longitude": -0.144879},
        )

    def test_result_language(self):
        """
        What3Words.geocode result language
        """
        result_geocode = self._make_request(
            self.geocoder.geocode,
            "piped.gains.jangle",
            lang='DE',

        )
        self.assertEqual(
            result_geocode.address,
            'unwesen.voll.schnitt'
        )






