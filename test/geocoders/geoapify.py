import pytest

from geopy.exc import GeocoderQueryError
from geopy.geocoders import Geoapify
from test.geocoders.util import BaseTestGeocoder, env


class TestGeoapify(BaseTestGeocoder):
    @classmethod
    def make_geocoder(cls):
        return Geoapify(
            api_key=env["GEOAPIFY_KEY"],
        )

    async def test_geocode_structured(self):
        query = {"street": "Viale Monza", "city": "Milano"}
        expected = {
            "latitude": 45.5209259,
            "longitude": 9.2272672,
            "address": "Viale Monza, 20126 Milan MI, Italy",
        }
        result = await self.geocode_run({"query": query}, expected)

        assert result.address == "Viale Monza, 20126 Milan MI, Italy"
        assert result.latitude == 45.5209259
        assert result.longitude == 9.2272672

    async def test_geocode_freetext(self):
        query = "38 Upper Montagu Street, London W1H 1LJ, United Kingdom"
        expected = {
            "latitude": 51.52016005,
            "longitude": -0.16030636023550826,
            "address": "38 Upper Montagu Street, London, W1H 1LJ, United Kingdom",
        }
        result = await self.geocode_run({"query": query}, expected)

        assert (
            result.address == "38 Upper Montagu Street, London, W1H 1LJ, United Kingdom"
        )
        assert result.latitude == 51.52016005
        assert result.longitude == -0.16030636023550826

    async def test_geocode_empty_res(self):
        query = {"street": "asfagsgsd", "city": "adgadfvad"}
        await self.geocode_run({"query": query}, {}, expect_failure=True)

    async def test_reverse(self):
        query = ("52.51894887928074", "13.409808180753316")
        expected = {
            "latitude": 52.51933485,
            "longitude": 13.410578611162324,
            "address": "RathausPassagen, Rathausstraße 1-14, 10178 Berlin, Germany",
        }
        result = await self.reverse_run({"query": query}, expected)

        assert (
            result.address
            == "RathausPassagen, Rathausstraße 1-14, 10178 Berlin, Germany"
        )
        assert result.latitude == 52.51933485
        assert result.longitude == 13.410578611162324


class TestUnitGeoapify:
    def test_api_key_ok(self):
        assert isinstance(Geoapify(api_key="abcd"), Geoapify)

    def test_parse_keyword_params_replace_underscores(self):
        params = {}
        params = Geoapify("abcd")._parse_keyword_params(params, filter_=1)
        assert params["filter"] == 1

    def test_addresslevel_is_type(self):
        params = {}
        params = Geoapify("abcd")._parse_keyword_params(params, type_=1)
        assert params["type"] == 1

    @pytest.mark.parametrize("limit", (1, 5, 100))
    def test_limit(self, limit):
        params = {}
        params = Geoapify("abcd")._parse_keyword_params(params, limit=limit)
        assert params["limit"] == limit

    def test_limit_raises_ValueError(self):
        with pytest.raises(ValueError) as e:
            Geoapify("abcd")._parse_keyword_params({}, exactly_one=False, limit=-10)

        assert str(e.value) == "Limit cannot be less than 1"

    @pytest.mark.parametrize("limit", (1, 5, 100))
    def test_limit_with_exactly_one_true(self, limit):
        params = {}
        params = Geoapify("abcd")._parse_keyword_params(
            params, exactly_one=True, limit=limit
        )
        assert params["limit"] == 1

    def test_parse_json_raises_GeocoderQueryError(self):
        result = {
            "statusCode": 401,
            "error": "Unauthorized",
            "message": "Invalid apiKey",
        }
        with pytest.raises(GeocoderQueryError):
            Geoapify("abcd")._parse_json(result, exactly_one=True)
