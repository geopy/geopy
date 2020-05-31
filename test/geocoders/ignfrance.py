# -*- coding: utf8 -*-
import unittest
from abc import ABCMeta, abstractmethod

import pytest
from six import with_metaclass

from geopy.exc import ConfigurationError, GeocoderQueryError
from geopy.geocoders import IGNFrance
from test.geocoders.util import GeocoderTestBase, env
from test.proxy_server import ProxyServerThread


class IGNFranceTestCaseUnitTest(GeocoderTestBase):

    def test_user_agent_custom(self):
        geocoder = IGNFrance(
            api_key='DUMMYKEY1234',
            username='MUSTERMANN',
            password='tops3cr3t',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    def test_invalid_auth_1(self):
        with pytest.raises(ConfigurationError):
            IGNFrance(api_key="a")

    def test_invalid_auth_2(self):
        with pytest.raises(ConfigurationError):
            IGNFrance(api_key="a", username="b", referer="c")

    def test_invalid_auth_3(self):
        with pytest.raises(ConfigurationError):
            IGNFrance(api_key="a", username="b")


class BaseIGNFranceTestCase(with_metaclass(ABCMeta, object)):

    @classmethod
    @abstractmethod
    def make_geocoder(cls, **kwargs):
        pass

    @classmethod
    def setUpClass(cls):
        cls.geocoder = cls.make_geocoder()

    def test_invalid_query_type(self):
        with pytest.raises(GeocoderQueryError):
            self.geocoder.geocode("44109000EX0114", query_type="invalid")

    def test_invalid_query_parcel(self):
        with pytest.raises(GeocoderQueryError):
            self.geocoder.geocode(
                "incorrect length string",
                query_type="CadastralParcel",
            )

    def test_geocode(self):
        self.geocode_run(
            {"query": "44109000EX0114",
             "query_type": "CadastralParcel",
             "exactly_one": True},
            {"latitude": 47.222482, "longitude": -1.556303},
        )

    def test_geocode_no_result(self):
        self.geocode_run(
            {"query": 'asdfasdfasdf'},
            {},
            expect_failure=True,
        )

    def test_reverse_no_result(self):
        self.reverse_run(
            # North Atlantic Ocean
            {"query": (35.173809, -37.485351), "exactly_one": True},
            {},
            expect_failure=True
        )

    def test_geocode_with_address(self):
        self.geocode_run(
            {"query": "Camp des Landes, 41200 VILLEFRANCHE-SUR-CHER",
             "query_type": "StreetAddress",
             "exactly_one": True},
            {"latitude": 47.293048,
             "longitude": 1.718985,
             "address": "le camp des landes, 41200 Villefranche-sur-Cher"},
        )

    def test_geocode_freeform(self):
        self.geocode_run(
            {"query": "8 rue Général Buat, Nantes",
             "query_type": "StreetAddress",
             "is_freeform": True,
             "exactly_one": True},
            {"address": "8 r general buat , 44000 Nantes"},
        )

    def test_geocode_position_of_interest(self):
        res = self.geocode_run(
            {"query": "Chambéry",
             "query_type": "PositionOfInterest",
             "exactly_one": False},
            {},
        )

        addresses = [location.address for location in res]
        assert "02000 Chambry" in addresses
        assert "16420 Saint-Christophe" in addresses

    def test_geocode_filter_by_attribute(self):
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

        assert len(unique) == 1
        assert unique[0] == "38"

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

        assert len(departements_no_spatial) > len(departements_spatial)

    def test_reverse(self):
        res = self.reverse_run(
            {"query": '47.229554,-1.541519',
             "exactly_one": True},
            {},
        )
        assert res.address == '7 av camille guerin, 44000 Nantes'

    def test_reverse_invalid_preference(self):
        with pytest.raises(GeocoderQueryError):
            self.geocoder.reverse(
                query='47.229554,-1.541519',
                exactly_one=True,
                reverse_geocode_preference=['a']  # invalid
            )

    def test_reverse_preference(self):
        res = self.reverse_run(
            {"query": '47.229554,-1.541519',
             "exactly_one": False,
             "reverse_geocode_preference": ['StreetAddress', 'PositionOfInterest']},
            {},
        )
        addresses = [location.address for location in res]
        assert "3 av camille guerin, 44000 Nantes" in addresses
        assert "5 av camille guerin, 44000 Nantes" in addresses

    def test_reverse_by_radius(self):
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

        assert coordinates_couples_radius.issubset(coordinates_couples)


@unittest.skipUnless(
    bool(env.get('IGNFRANCE_KEY') and env.get('IGNFRANCE_REFERER')),
    "No IGNFRANCE_KEY or IGNFRANCE_REFERER env variable set"
)
class IGNFranceApiKeyAuthTestCase(BaseIGNFranceTestCase, GeocoderTestBase):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return IGNFrance(
            api_key=env['IGNFRANCE_KEY'],
            referer=env['IGNFRANCE_REFERER'],
            timeout=10
        )


@unittest.skipUnless(
    bool(env.get('IGNFRANCE_USERNAME_KEY') and env.get('IGNFRANCE_USERNAME')
         and env.get('IGNFRANCE_PASSWORD')),
    "No IGNFRANCE_USERNAME_KEY or IGNFRANCE_USERNAME "
    "or IGNFRANCE_PASSWORD env variable set"
)
class IGNFranceUsernameAuthTestCase(BaseIGNFranceTestCase, GeocoderTestBase):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return IGNFrance(
            api_key=env['IGNFRANCE_USERNAME_KEY'],
            username=env['IGNFRANCE_USERNAME'],
            password=env['IGNFRANCE_PASSWORD'],
            timeout=10
        )


@unittest.skipUnless(
    bool(env.get('IGNFRANCE_USERNAME_KEY') and env.get('IGNFRANCE_USERNAME')
         and env.get('IGNFRANCE_PASSWORD')),
    "No IGNFRANCE_USERNAME_KEY or IGNFRANCE_USERNAME "
    "or IGNFRANCE_PASSWORD env variable set"
)
class IGNFranceUsernameAuthProxyTestCase(GeocoderTestBase):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return IGNFrance(
            api_key=env['IGNFRANCE_USERNAME_KEY'],
            username=env['IGNFRANCE_USERNAME'],
            password=env['IGNFRANCE_PASSWORD'],
            timeout=10,
            **kwargs
        )

    proxy_timeout = 5

    def setUp(self):
        self.proxy_server = ProxyServerThread(timeout=self.proxy_timeout)
        self.proxy_server.start()
        self.proxy_url = self.proxy_server.get_proxy_url()
        self.geocoder = self.make_geocoder(proxies=self.proxy_url)

    def tearDown(self):
        self.proxy_server.stop()
        self.proxy_server.join()

    def test_proxy_is_respected(self):
        assert 0 == len(self.proxy_server.requests)
        self.geocode_run(
            {"query": "Camp des Landes, 41200 VILLEFRANCHE-SUR-CHER",
             "query_type": "StreetAddress",
             "exactly_one": True},
            {"latitude": 47.293048,
             "longitude": 1.718985,
             "address": "le camp des landes, 41200 Villefranche-sur-Cher"},
        )
        assert 1 == len(self.proxy_server.requests)
