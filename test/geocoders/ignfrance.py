import pytest

from geopy.exc import GeocoderQueryError
from geopy.geocoders import IGNFrance
from test.geocoders.util import BaseTestGeocoder
from test.proxy_server import ProxyServerThread


class TestIGNFrance(BaseTestGeocoder):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return IGNFrance(
            timeout=10
        )

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


class TestIGNFranceUsernameAuthProxy(BaseTestGeocoder):
    proxy_timeout = 5

    @classmethod
    def make_geocoder(cls, **kwargs):
        return IGNFrance(
            timeout=10,
            **kwargs
        )

    @pytest.fixture(scope='class', autouse=True)
    async def start_proxy(_, request, class_geocoder):
        cls = request.cls
        cls.proxy_server = ProxyServerThread(timeout=cls.proxy_timeout)
        cls.proxy_server.start()
        cls.proxy_url = cls.proxy_server.get_proxy_url()
        async with cls.inject_geocoder(cls.make_geocoder(proxies=cls.proxy_url)):
            yield
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
