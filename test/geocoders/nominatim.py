import warnings
from unittest.mock import patch

import pytest

import geopy.geocoders
from geopy.exc import ConfigurationError
from geopy.geocoders import Nominatim
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder


class BaseTestNominatim(BaseTestGeocoder):
    # Common test cases for Nominatim-based geocoders.
    # Assumes that Nominatim uses the OSM data.

    delta = 0.04

    async def test_geocode(self):
        await self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    async def test_geocode_empty_result(self):
        await self.geocode_run(
            {"query": "dsadjkasdjasd"},
            {},
            expect_failure=True,
        )

    async def test_reverse_empty_result(self):
        await self.reverse_run(
            {"query": Point(0.05, -0.15)},
            {},
            expect_failure=True,
        )

    async def test_limit(self):
        with pytest.raises(ValueError):  # non-positive limit
            await self.geocode_run(
                {"query": "does not matter", "limit": 0, "exactly_one": False},
                {}
            )

        result = await self.geocode_run(
            {"query": "second street", "limit": 4, "exactly_one": False},
            {}
        )
        assert len(result) >= 3  # PickPoint sometimes returns 3
        assert 4 >= len(result)

    @patch.object(geopy.geocoders.options, 'default_user_agent',
                  'mocked_user_agent/0.0.0')
    def test_user_agent_default(self):
        geocoder = self.make_geocoder(user_agent=None)
        assert geocoder.headers['User-Agent'] == 'mocked_user_agent/0.0.0'

    async def test_user_agent_custom(self):
        geocoder = self.make_geocoder(
            user_agent='my_test_application'
        )
        assert geocoder.headers['User-Agent'] == 'my_test_application'

    async def test_reverse(self):
        location = await self.reverse_run(
            {"query": Point(40.75376406311989, -73.98489005863667)},
            {"latitude": 40.753, "longitude": -73.984}
        )
        assert "New York" in location.address

    async def test_reverse_near_zero(self):
        location = await self.reverse_run(
            {"query": Point(31.0, -1.0e-5)},
            {"latitude": 32.3096365, "longitude": 0.2450916, "delta": 3}
        )
        assert "El Bayadh" in location.address

    async def test_structured_query(self):
        await self.geocode_run(
            {"query": {"country": "us", "city": "moscow",
                       "state": "idaho"}},
            {"latitude": 46.7323875, "longitude": -117.0001651},
        )

    async def test_city_district_with_dict_query(self):
        query = {'postalcode': 10117}
        result = await self.geocode_run(
            {"query": query, "addressdetails": True, "country_codes": "DE"},
            {},
        )
        try:
            # For some queries `city_district` might be missing in the response.
            # For this specific query on OpenMapQuest the key is also missing.
            assert 'Mitte' == result.raw['address']['city_district']
        except KeyError:
            # MapQuest
            try:
                assert 'Mitte' == result.raw['address']['suburb']
            except KeyError:
                # PickPoint
                assert 'Deutschland' == result.raw['address']['country']
                # {'postcode': '10117', 'country': 'Deutschland', 'country_code': 'de'}

    async def test_geocode_language_parameter(self):
        query = "Mohrenstrasse Berlin"
        result_geocode = await self.geocode_run(
            {"query": query, "addressdetails": True,
             "language": "de"},
            {},
        )
        assert result_geocode.raw['address']['country'] == "Deutschland"
        result_geocode = await self.geocode_run(
            {"query": query, "addressdetails": True,
             "language": "en"},
            {},
        )
        assert result_geocode.raw['address']['country'] == "Germany"

    async def test_reverse_language_parameter(self):
        query = "52.51693903613385, 13.3859332733135"
        result_reverse_de = await self.reverse_run(
            {"query": query, "language": "de"},
            {},
        )
        assert result_reverse_de.raw['address']['country'] == "Deutschland"

        result_reverse_en = await self.reverse_run(
            {"query": query, "language": "en"},
            {},
        )
        # have had a change in the exact authority name
        assert "Germany" in result_reverse_en.raw['address']['country']

    async def test_geocode_geometry_wkt(self):
        result_geocode = await self.geocode_run(
            {"query": "Halensee,Berlin", "geometry": 'WKT'},
            {},
        )
        assert result_geocode.raw['geotext'].startswith('POLYGON((')

    async def test_geocode_geometry_svg(self):
        result_geocode = await self.geocode_run(
            {"query": "Halensee,Berlin", "geometry": 'svg'},
            {},
        )
        assert result_geocode.raw['svg'].startswith('M 13.')

    async def test_geocode_geometry_kml(self):
        result_geocode = await self.geocode_run(
            {"query": "Halensee,Berlin", "geometry": 'kml'},
            {},
        )
        assert result_geocode.raw['geokml'].startswith('<Polygon>')

    async def test_geocode_geometry_geojson(self):
        result_geocode = await self.geocode_run(
            {"query": "Halensee,Berlin", "geometry": 'geojson'},
            {},
        )
        assert result_geocode.raw['geojson'].get('type') == 'Polygon'

    async def test_missing_reverse_details(self):
        query = (46.46131, 6.84311)
        res = await self.reverse_run(
            {"query": query},
            {}
        )
        assert "address" in res.raw

        res = await self.reverse_run(
            {"query": query, "addressdetails": False},
            {},
        )
        assert 'address' not in res.raw

    async def test_viewbox(self):
        res = await self.geocode_run(
            {"query": "Maple Street"},
            {},
        )
        assert not (50 <= res.latitude <= 52)
        assert not (-0.15 <= res.longitude <= -0.11)

        for viewbox in [
            ((52, -0.11), (50, -0.15)),
            [Point(52, -0.11), Point(50, -0.15)],
            (("52", "-0.11"), ("50", "-0.15"))
        ]:
            await self.geocode_run(
                {"query": "Maple Street", "viewbox": viewbox},
                {"latitude": 51.5223513, "longitude": -0.1382104}
            )

    async def test_bounded(self):
        bb = (Point('56.588456', '84.719353'), Point('56.437293', '85.296822'))
        query = (
            '\u0441\u0442\u0440\u043e\u0438\u0442\u0435\u043b\u044c '
            '\u0442\u043e\u043c\u0441\u043a'
        )

        await self.geocode_run(
            {"query": query, "viewbox": bb},
            {"latitude": 56.4129459, "longitude": 84.847831069814, "delta": 1.0},
        )

        await self.geocode_run(
            {"query": query, "viewbox": bb, "bounded": True},
            {"latitude": 56.4803224, "longitude": 85.0060457653324},
        )

    async def test_extratags(self):
        query = "Statue of Liberty"
        location = await self.geocode_run(
            {"query": query},
            {},
        )
        assert location.raw.get('extratags') is None
        location = await self.geocode_run(
            {"query": query, "extratags": True},
            {},
        )

        # 'wikidata': 'Q9202', 'wikipedia': 'en:Statue of Liberty'
        assert location.raw['extratags']['wikidata'] == 'Q9202'

    async def test_country_codes_moscow(self):
        await self.geocode_run(
            {"query": "moscow", "country_codes": "RU"},
            {"latitude": 55.7507178, "longitude": 37.6176606,
             "delta": 0.3},
        )

        location = await self.geocode_run(
            {"query": "moscow", "country_codes": "US"},
            # There are two possible results:
            # Moscow Idaho: 46.7323875,-117.0001651
            # Moscow Penn: 41.3367497,-75.5185191
            {},
        )
        # We don't care which Moscow is returned, unless it's
        # the Russian one. We can sort this out by asserting
        # the longitudes. The Russian Moscow has positive longitudes.
        assert -119 < location.longitude
        assert location.longitude < -70

    async def test_country_codes_str(self):
        await self.geocode_run(
            {"query": "kazan",
             "country_codes": 'tr'},
            {"latitude": 40.2317, "longitude": 38.0, "delta": 15},
        )

    async def test_country_codes_list(self):
        await self.geocode_run(
            {"query": "kazan",
             "country_codes": ['cn', 'tr']},
            {"latitude": 40.2317, "longitude": 38.0, "delta": 15},
        )

    @pytest.mark.parametrize(
        "payload, expected",
        [
            pytest.param(
                {"query": "mexico", "featuretype": 'country'},
                {"latitude": 22.5000485, "longitude": -100.0000375, "delta": 5.0},
                id="country",
            ),
            pytest.param(
                {"query": "mexico", "featuretype": 'state', "country_codes": "US"},
                {"latitude": 34.5708167, "longitude": -105.993007, "delta": 2.0},
                id="state",
                marks=pytest.mark.xfail(reason='OSM responds incorrectly here'),
            ),
            pytest.param(
                {"query": "mexico", "featuretype": 'city'},
                {"latitude": 19.4326009, "longitude": -99.1333416, "delta": 2.0},
                id="city",
                marks=pytest.mark.xfail(reason='OSM responds incorrectly here'),
            ),
            pytest.param(
                {"query": "georgia", "featuretype": 'settlement'},
                {"latitude": 32.3293809, "longitude": -83.1137366, "delta": 2.0},
                id="settlement",
                marks=pytest.mark.xfail(reason='OSM responds incorrectly here'),
            ),
        ]
    )
    async def test_featuretype_param(self, payload, expected):
        await self.geocode_run(payload, expected)

    async def test_geocode_namedetails(self):
        query = "Kyoto, Japan"
        result = await self.geocode_run(
            {"query": query, "namedetails": True},
            {},
        )
        assert 'namedetails' in result.raw

        result = await self.geocode_run(
            {"query": query, "namedetails": False},
            {},
        )
        assert 'namedetails' not in result.raw

    async def test_reverse_namedetails(self):
        query = "40.689253199999996, -74.04454817144321"
        result = await self.reverse_run(
            {"query": query, "namedetails": True},
            {},
        )
        assert 'namedetails' in result.raw

        result = await self.reverse_run(
            {"query": query, "namedetails": False},
            {},
        )
        assert 'namedetails' not in result.raw

    async def test_reverse_zoom_parameter(self):
        query = "40.689253199999996, -74.04454817144321"
        result_reverse = await self.reverse_run(
            {"query": query, "zoom": 10},
            {},
        )
        assert "New York" in result_reverse.address
        assert "Statue of Liberty" not in result_reverse.address

        result_reverse = await self.reverse_run(
            {"query": query},
            {},
        )
        assert "New York" in result_reverse.address
        try:
            # Pickpoint
            assert "Statue of Liberty" in result_reverse.address
        except AssertionError:
            # Nominatim
            assert "Flagpole Plaza" in result_reverse.address


class TestNominatim(BaseTestNominatim):

    @classmethod
    def make_geocoder(cls, **kwargs):
        kwargs.setdefault('user_agent', 'geopy-test')
        return Nominatim(**kwargs)

    async def test_default_user_agent_error(self):
        with pytest.raises(ConfigurationError):
            Nominatim()

    async def test_example_user_agent_error(self):
        with pytest.raises(ConfigurationError):
            Nominatim(user_agent="specify_your_app_name_here")

    async def test_custom_user_agent_works(self):
        Nominatim(user_agent='my_application')

        with patch.object(geopy.geocoders.options, 'default_user_agent',
                          'my_application'):
            Nominatim()

    def test_import_deprecated_osm_module(self):
        with warnings.catch_warnings(record=True) as w:
            from geopy.geocoders.osm import Nominatim as OsmNominatim
        assert len(w) == 1
        assert OsmNominatim is Nominatim
