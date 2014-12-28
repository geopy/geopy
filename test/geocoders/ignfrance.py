# -*- coding: utf8 -*-
import unittest

from geopy.compat import py3k
from geopy.geocoders import IGNFrance
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(  # pylint: disable=R0904,C0111
    bool((env.get('IGNFRANCE_KEY') and
          env.get('IGNFRANCE_USERNAME') and
          env.get('IGNFRANCE_PASSWORD')) or
         (env.get('IGNFRANCE_KEY') and
          env.get('IGNFRANCE_REFERER'))),
    "One or more of the env variables IGNFRANCE_KEY, IGNFRANCE_USERNAME \
    and IGNFRANCE_PASSWORD is not set"
)
class IGNFranceTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = IGNFrance(
            api_key=env.get('IGNFRANCE_KEY'),
            username=env.get('IGNFRANCE_USERNAME'),
            password=env.get('IGNFRANCE_PASSWORD'),
            referer=env.get('IGNFRANCE_REFERER'),
            timeout=20
        )
        cls.delta_exact = 0.2

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
    def test_geocode_freeform(self):
        """
        IGNFrance.geocode with freeform and StreetAddress
        """
        res = self._make_request(
            self.geocoder.geocode,
            query="8 rue Général Buat, Nantes",
            query_type="StreetAddress",
            is_freeform=True,
            exactly_one=True
        )

        if res is None:
            unittest.SkipTest("IGN France API sometimes returns no result")
        else:
            self.assertEqual(
                res.address,
                "8 r general buat , 44000 Nantes"
            )

    def test_geocode_position_of_interest(self):
        """
        IGNFrance.geocode with PositionOfInterest
        """
        res = self._make_request(
            self.geocoder.geocode,
            query="Chambéry",
            query_type="PositionOfInterest",
            exactly_one=False
        )

        if res is None:
            unittest.SkipTest("IGN France API sometimes returns no result")
        else:
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
        res = self._make_request(
            self.geocoder.geocode,
            query="Les Molettes",
            query_type="PositionOfInterest",
            maximum_responses=10,
            filtering='<Place type="Departement">38</Place>',
            exactly_one=False
        )

        if res is None:
            unittest.SkipTest("IGN France API sometimes returns no result")
        else:
            departements = [location.raw['departement'] for location in res]
            unique = list(set(departements))

            self.assertEqual(
                len(unique),
                1
            )
            self.assertEqual(
                unique[0],
                "38"
            )

    def test_geocode_filter_by_envelope(self):
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

        res_spatial_filter = self._make_request(
            self.geocoder.geocode,
            'Les Molettes',
            'PositionOfInterest',
            maximum_responses=10,
            filtering=spatial_filtering_envelope,
            exactly_one=False
        )

        
        departements_spatial = list(
            set([
                i.raw['departement']
                for i in res_spatial_filter
            ])
        )

        res_no_spatial_filter = self._make_request(
            self.geocoder.geocode,
            'Les Molettes',
            'PositionOfInterest',
            maximum_responses=10,
            exactly_one=False
        )

        departements_no_spatial = list(
            set([
                i.raw['departement']
                for i in res_no_spatial_filter
            ])
        )

        if res_no_spatial_filter is None or res_spatial_filter is None:
            unittest.SkipTest("IGN France API sometimes returns no result")
        else:
            self.assertGreater(
                len(departements_no_spatial),
                len(departements_spatial)
            )

    def test_reverse(self):
        """
        IGNFrance.reverse simple
        """
        res = self._make_request(
            self.geocoder.reverse,
            query='47.229554,-1.541519',
            exactly_one=True
        )

        if res is None:
            unittest.SkipTest("IGN France API sometimes returns no result")
        else:
            self.assertEqual(
                res.address,
                '3 av camille guerin, 44000 Nantes'
            )

    def test_reverse_preference(self):
        """
        IGNFrance.reverse preference
        """
        res = self._make_request(
            self.geocoder.reverse,
            query='47.229554,-1.541519',
            reverse_geocode_preference=['StreetAddress', 'PositionOfInterest']
        )

        if res is None:
            unittest.SkipTest("IGN France API sometimes returns no result")
        else:
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

        res_call_radius = self._make_request(
            self.geocoder.reverse,
            query='48.8033333,2.3241667',
            maximum_responses=10,
            filtering=spatial_filtering_radius)

        res_call = self._make_request(
            self.geocoder.reverse,
            query='48.8033333,2.3241667',
            maximum_responses=10
        )

        if res_call_radius is None or res_call is None:
            unittest.SkipTest("IGN France API sometimes returns no result")
        else:
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
