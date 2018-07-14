# -*- coding: utf8 -*-
import unittest

from geopy.exc import ConfigurationError, GeocoderQueryError
from geopy.geocoders import IGNFrance
from test.geocoders.util import GeocoderTestBase, env

credentials = bool(
    (env.get('IGNFRANCE_KEY') and env.get('IGNFRANCE_USERNAME')
     and env.get('IGNFRANCE_PASSWORD')) or (
         env.get('IGNFRANCE_KEY') and env.get('IGNFRANCE_REFERER'))
)


class IGNFranceTestCaseUnitTest(GeocoderTestBase):

    def test_user_agent_custom(self):
        geocoder = IGNFrance(
            api_key='DUMMYKEY1234',
            username='MUSTERMANN',
            password='tops3cr3t',
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')


@unittest.skipUnless(
    credentials,
    "One or more of the env variables IGNFRANCE_KEY, IGNFRANCE_USERNAME "
    "and IGNFRANCE_PASSWORD is not set"
)
class IGNFranceTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        if not credentials:
            return
        cls.geocoder = IGNFrance(
            api_key=env.get('IGNFRANCE_KEY'),
            username=env.get('IGNFRANCE_USERNAME'),
            password=env.get('IGNFRANCE_PASSWORD'),
            referer=env.get('IGNFRANCE_REFERER'),
            timeout=10
        )
        cls.delta_exact = 0.2

    def test_invalid_auth_1(self):
        """
        IGNFrance api_key without referer is ConfigurationError
        """
        with self.assertRaises(ConfigurationError):
            IGNFrance(api_key="a")

    def test_invalid_auth_2(self):
        """
        IGNFrance api_key, username, and referer is ConfigurationError
        """
        with self.assertRaises(ConfigurationError):
            IGNFrance(api_key="a", username="b", referer="c")

    def test_invalid_auth_3(self):
        """
        IGNFrance username without password is ConfgurationError
        """
        with self.assertRaises(ConfigurationError):
            IGNFrance(api_key="a", username="b")

    def test_invalid_query_type(self):
        """
        IGNFrance.geocode invalid query_type
        """
        with self.assertRaises(GeocoderQueryError):
            self.geocoder.geocode("44109000EX0114", query_type="invalid")

    def test_invalid_query_parcel(self):
        """
        IGNFrance.geocode invalid CadastralParcel
        """
        with self.assertRaises(GeocoderQueryError):
            self.geocoder.geocode(
                "incorrect length string",
                query_type="CadastralParcel",
            )

    def test_geocode(self):
        """
        IGNFrance.geocode CadastralParcel
        """
        self.geocode_run(
            {"query": "44109000EX0114",
             "query_type": "CadastralParcel",
             "exactly_one": True},
            {"latitude": 47.222482, "longitude": -1.556303},
        )

    def test_geocode_with_address(self):
        """
        IGNFrance.geocode Address
        """
        self.geocode_run(
            {"query": "Camp des Landes, 41200 VILLEFRANCHE-SUR-CHER",
             "query_type": "StreetAddress",
             "exactly_one": True},
            {"latitude": 47.293048,
             "longitude": 1.718985,
             "address": "le camp des landes, 41200 Villefranche-sur-Cher"},
        )

    def test_geocode_freeform(self):
        """
        IGNFrance.geocode with freeform and StreetAddress
        """
        self.geocode_run(
            {"query": "8 rue Général Buat, Nantes",
             "query_type": "StreetAddress",
             "is_freeform": True,
             "exactly_one": True},
            {"address": "8 r general buat , 44000 Nantes"},
        )

    def test_geocode_position_of_interest(self):
        """
        IGNFrance.geocode with PositionOfInterest
        """
        res = self.geocode_run(
            {"query": "Chambéry",
             "query_type": "PositionOfInterest",
             "exactly_one": False},
            {},
        )

        self.assertEqual(
            res[0].address,
            "02000 Chambry"
        )
        self.assertEqual(
            res[1].address,
            "16420 Saint-Christophe"
        )

    def test_geocode_filter_by_attribute(self):
        """
        IGNFrance.geocode with filter by attribute
        """
        res = self.geocode_run(
            {"query": "Les Molettes",
             "query_type": "PositionOfInterest",
             "maximum_responses": 10,
             "filtering": '<Place type="Departement">38</Place>',
             "exactly_one": False},
            {},
        )

        departements = [location.raw['departement'] for location in res]
        unique = list(set(departements))

        self.assertEqual(len(unique), 1)
        self.assertEqual(unique[0], "38")

    def test_geocode_filter_by_envelope(self):
        """
        IGNFrance.geocode using envelope
        """
        lat_min, lng_min, lat_max, lng_max = 45.00, 5, 46, 6.40

        spatial_filtering_envelope = """
        <gml:envelope>
            <gml:pos>{lat_min} {lng_min}</gml:pos>
            <gml:pos>{lat_max} {lng_max}</gml:pos>
        </gml:envelope>
        """.format(
            lat_min=lat_min,
            lng_min=lng_min,
            lat_max=lat_max,
            lng_max=lng_max
        )

        res_spatial_filter = self.geocode_run(
            {"query": 'Les Molettes',
             "query_type": 'PositionOfInterest',
             "maximum_responses": 10,
             "filtering": spatial_filtering_envelope,
             "exactly_one": False},
            {},
        )

        departements_spatial = list(
            {i.raw['departement'] for i in res_spatial_filter}
        )

        res_no_spatial_filter = self.geocode_run(
            {"query": 'Les Molettes',
             "query_type": 'PositionOfInterest',
             "maximum_responses": 10,
             "exactly_one": False},
            {},
        )

        departements_no_spatial = list(
            set([
                i.raw['departement']
                for i in res_no_spatial_filter
            ])
        )

        self.assertGreater(
            len(departements_no_spatial),
            len(departements_spatial)
        )

    def test_reverse(self):
        """
        IGNFrance.reverse simple
        """
        res = self.reverse_run(
            {"query": '47.229554,-1.541519',
             "exactly_one": True},
            {},
        )
        self.assertEqual(
            res.address,
            '3 av camille guerin, 44000 Nantes'
        )

    def test_reverse_invalid_preference(self):
        """
        IGNFrance.reverse with invalid reverse_geocode_preference
        """
        with self.assertRaises(GeocoderQueryError):
            self.geocoder.reverse(
                query='47.229554,-1.541519',
                exactly_one=True,
                reverse_geocode_preference=['a']
            )

    def test_reverse_preference(self):
        """
        IGNFrance.reverse preference
        """
        res = self.reverse_run(
            {"query": '47.229554,-1.541519',
             "exactly_one": False,
             "reverse_geocode_preference": ['StreetAddress', 'PositionOfInterest']},
            {},
        )
        self.assertEqual(
            res[0].address,
            '3 av camille guerin, 44000 Nantes'
        )
        self.assertEqual(
            res[1].address,
            '5 av camille guerin, 44000 Nantes'
        )

    def test_reverse_by_radius(self):
        """
        IGNFrance.reverse by radius
        """
        spatial_filtering_radius = """
        <gml:CircleByCenterPoint>
            <gml:pos>{coord}</gml:pos>
            <gml:radius>{radius}</gml:radius>
        </gml:CircleByCenterPoint>
        """.format(coord='48.8033333 2.3241667', radius='50')

        res_call_radius = self.reverse_run(
            {"query": '48.8033333,2.3241667',
             "exactly_one": False,
             "maximum_responses": 10,
             "filtering": spatial_filtering_radius},
            {},
        )

        res_call = self.reverse_run(
            {"query": '48.8033333,2.3241667',
             "exactly_one": False,
             "maximum_responses": 10},
            {},
        )

        coordinates_couples_radius = set([
            (str(location.latitude) + ' ' + str(location.longitude))
            for location in res_call_radius
        ])
        coordinates_couples = set([
            (str(location.latitude) + ' ' + str(location.longitude))
            for location in res_call
        ])

        self.assertEqual(
            coordinates_couples_radius.issubset(coordinates_couples),
            True
        )
