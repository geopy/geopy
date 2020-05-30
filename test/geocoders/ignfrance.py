import pytest
from async_generator import async_generator, yield_

from geopy.exc import ConfigurationError, GeocoderQueryError
from geopy.geocoders import IGNFrance
from test.geocoders.util import BaseTestGeocoder, env
from test.proxy_server import ProxyServerThread


class TestUnitIGNFrance:

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


class BaseTestIGNFrance(BaseTestGeocoder):

    async def test_invalid_query_type(self):
        with pytest.raises(GeocoderQueryError):
            self.geocoder.geocode("44109000EX0114", query_type="invalid")

    async def test_invalid_query_parcel(self):
        with pytest.raises(GeocoderQueryError):
            self.geocoder.geocode(
                "incorrect length string",
                query_type="CadastralParcel",
            )

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "44109000EX0114",
             "query_type": "CadastralParcel"},
            {"latitude": 47.222482, "longitude": -1.556303},
        )

    async def test_geocode_no_result(self):
        await self.geocode_run(
            {"query": 'asdfasdfasdf'},
            {},
            expect_failure=True,
        )

    async def test_reverse_no_result(self):
        await self.reverse_run(
            # North Atlantic Ocean
            {"query": (35.173809, -37.485351)},
            {},
            expect_failure=True
        )

    async def test_geocode_with_address(self):
        await self.geocode_run(
            {"query": "Camp des Landes, 41200 VILLEFRANCHE-SUR-CHER",
             "query_type": "StreetAddress"},
            {"latitude": 47.293048,
             "longitude": 1.718985,
             "address": "le camp des landes, 41200 Villefranche-sur-Cher"},
        )

    async def test_geocode_freeform(self):
        await self.geocode_run(
            {"query": "8 rue Général Buat, Nantes",
             "query_type": "StreetAddress",
             "is_freeform": True},
            {"address": "8 r general buat , 44000 Nantes"},
        )

    async def test_geocode_position_of_interest(self):
        res = await self.geocode_run(
            {"query": "Chambéry",
             "query_type": "PositionOfInterest",
             "exactly_one": False},
            {},
        )

        addresses = [location.address for location in res]
        assert "02000 Chambry" in addresses
        assert "16420 Saint-Christophe" in addresses

    async def test_geocode_filter_by_attribute(self):
        res = await self.geocode_run(
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

    async def test_geocode_filter_by_envelope(self):
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

        res_spatial_filter = await self.geocode_run(
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

        res_no_spatial_filter = await self.geocode_run(
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

    async def test_reverse(self):
        res = await self.reverse_run(
            {"query": '47.229554,-1.541519'},
            {},
        )
        assert res.address == '7 av camille guerin, 44000 Nantes'

    async def test_reverse_invalid_preference(self):
        with pytest.raises(GeocoderQueryError):
            self.geocoder.reverse(
                query='47.229554,-1.541519',
                reverse_geocode_preference=['a']  # invalid
            )

    async def test_reverse_preference(self):
        res = await self.reverse_run(
            {"query": '47.229554,-1.541519',
             "exactly_one": False,
             "reverse_geocode_preference": ['StreetAddress', 'PositionOfInterest']},
            {},
        )
        addresses = [location.address for location in res]
        assert "3 av camille guerin, 44000 Nantes" in addresses
        assert "5 av camille guerin, 44000 Nantes" in addresses

    async def test_reverse_by_radius(self):
        spatial_filtering_radius = """
        <gml:CircleByCenterPoint>
            <gml:pos>{coord}</gml:pos>
            <gml:radius>{radius}</gml:radius>
        </gml:CircleByCenterPoint>
        """.format(coord='48.8033333 2.3241667', radius='50')

        res_call_radius = await self.reverse_run(
            {"query": '48.8033333,2.3241667',
             "exactly_one": False,
             "maximum_responses": 10,
             "filtering": spatial_filtering_radius},
            {},
        )

        res_call = await self.reverse_run(
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


@pytest.mark.skipif(
    not bool(env.get('IGNFRANCE_KEY') and env.get('IGNFRANCE_REFERER')),
    reason="No IGNFRANCE_KEY or IGNFRANCE_REFERER env variable set"
)
class TestIGNFranceApiKeyAuth(BaseTestIGNFrance):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return IGNFrance(
            api_key=env['IGNFRANCE_KEY'],
            referer=env['IGNFRANCE_REFERER'],
            timeout=10
        )


@pytest.mark.skipif(
    not bool(env.get('IGNFRANCE_USERNAME_KEY') and env.get('IGNFRANCE_USERNAME')
             and env.get('IGNFRANCE_PASSWORD')),
    reason="No IGNFRANCE_USERNAME_KEY or IGNFRANCE_USERNAME "
    "or IGNFRANCE_PASSWORD env variable set"
)
class TestIGNFranceUsernameAuth(BaseTestIGNFrance):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return IGNFrance(
            api_key=env['IGNFRANCE_USERNAME_KEY'],
            username=env['IGNFRANCE_USERNAME'],
            password=env['IGNFRANCE_PASSWORD'],
            timeout=10,
            **kwargs
        )


@pytest.mark.skipif(
    not bool(env.get('IGNFRANCE_USERNAME_KEY') and env.get('IGNFRANCE_USERNAME')
             and env.get('IGNFRANCE_PASSWORD')),
    reason="No IGNFRANCE_USERNAME_KEY or IGNFRANCE_USERNAME "
    "or IGNFRANCE_PASSWORD env variable set"
)
class TestIGNFranceUsernameAuthProxy(BaseTestGeocoder):
    proxy_timeout = 5

    @classmethod
    def make_geocoder(cls, **kwargs):
        return IGNFrance(
            api_key=env['IGNFRANCE_USERNAME_KEY'],
            username=env['IGNFRANCE_USERNAME'],
            password=env['IGNFRANCE_PASSWORD'],
            timeout=10,
            **kwargs
        )

    @pytest.fixture(scope='class', autouse=True)
    @async_generator
    async def start_proxy(_, request, class_geocoder):
        cls = request.cls
        cls.proxy_server = ProxyServerThread(timeout=cls.proxy_timeout)
        cls.proxy_server.start()
        cls.proxy_url = cls.proxy_server.get_proxy_url()
        async with cls.inject_geocoder(cls.make_geocoder(proxies=cls.proxy_url)):
            await yield_()
        cls.proxy_server.stop()
        cls.proxy_server.join()

    async def test_proxy_is_respected(self):
        assert 0 == len(self.proxy_server.requests)
        await self.geocode_run(
            {"query": "Camp des Landes, 41200 VILLEFRANCHE-SUR-CHER",
             "query_type": "StreetAddress"},
            {"latitude": 47.293048,
             "longitude": 1.718985,
             "address": "le camp des landes, 41200 Villefranche-sur-Cher"},
        )
        assert 1 == len(self.proxy_server.requests)
