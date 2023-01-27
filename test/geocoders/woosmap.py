import pytest

from geopy import exc
from geopy.geocoders import Woosmap
from geopy.point import Point
from test.geocoders.util import BaseTestGeocoder, env


class TestWoosmap(BaseTestGeocoder):
    london_point = Point(51.50940214, -0.133012)
    address_query = "12 Oxford Street, London"

    @classmethod
    def make_geocoder(cls, **kwargs):
        return Woosmap(api_key=env['WOOSMAP_KEY'], **kwargs)

    async def test_user_agent_custom(self):
        geocoder = Woosmap(
            api_key='DUMMYPRIVATEKEY1234',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    async def test_error_with_no_api_key(self):
        with pytest.raises(exc.ConfigurationError):
            Woosmap()

    async def test_check_status(self):
        def make_status(status):
            return {
                "status": status,
            }

        assert self.geocoder._check_status(make_status("ZERO_RESULTS")) is None
        with pytest.raises(exc.GeocoderQueryError):
            self.geocoder._check_status(make_status("INVALID_REQUEST"))
        with pytest.raises(exc.GeocoderQueryError):
            self.geocoder._check_status(make_status("REQUEST_DENIED"))
        with pytest.raises(exc.GeocoderServiceError):
            self.geocoder._check_status(make_status("UNKNOWN_ERROR"))
        with pytest.raises(exc.GeocoderServiceError):
            self.geocoder._check_status(make_status("DUMMY_ERROR"))

    async def test_format_components_param(self):
        f = self.geocoder._format_components_param
        assert f({}) == ''
        assert f([]) == ''

        assert f([('country', 'FR')]) == 'country:FR'
        output = f([
            ('country', 'DE'),
            ('country', 'GB'),
            ('country', 'US')
        ])
        assert (
            output ==
            'country:DE|country:GB|country:US'
        )

        with pytest.raises(ValueError):
            f(None)

        with pytest.raises(ValueError):
            f('country:DE|country:FR')

    async def test_geocode(self):
        await self.geocode_run(
            {"query": self.address_query},
            {"latitude": 51.51652, "longitude": -0.131},
        )

    async def test_geocode_with_components(self):
        await self.geocode_run(
            {
                "query": "paris",
                "components": {
                    "country": "FR"
                }
            },
            {"latitude": 48.85717, "longitude": 2.3414},
        )

        await self.geocode_run(
            {
                "query": "paris",
                "components": [
                    ('country', 'US')
                ]
            },
            {"latitude": 33.66128, "longitude": -95.56356},
        )

    async def test_geocode_with_location_bias(self):
        await self.geocode_run(
            {
                "query": "paris",  # Texas USA
                "location": (33.65919, -95.55486)
            },
            {"latitude": 33.66128, "longitude": -95.56356},
        )

    async def test_geocode_with_language(self):
        result = await self.geocode_run(
            {"query": self.address_query, "language": "fr"},
            {}
        )
        assert "Royaume-Uni" in result.address

        result = await self.geocode_run(
            {"query": self.address_query, "language": "en"},
            {}
        )
        assert "United Kingdom" in result.address

    async def test_geocode_with_cc_format(self):
        result = await self.geocode_run(
            {"query": self.address_query, "cc_format": "alpha3"},
            {}
        )
        country_component = [comp for comp in result.raw["address_components"] if
                             'country' in comp['types']][0]
        assert country_component.get('short_name') == "GBR"

        result = await self.geocode_run(
            {"query": self.address_query, "cc_format": "alpha2"},
            {}
        )
        country_component = [comp for comp in result.raw["address_components"] if
                             'country' in comp['types']][0]
        assert country_component.get('short_name') == "GB"

    async def test_geocode_limit(self):
        result = await self.geocode_run(
            {
                "query": "oxford street",
                "limit": 5,
                "exactly_one": False
            },
            {}
        )
        assert len(result) == 5

    async def test_reverse(self):
        await self.reverse_run(
            {"query": self.london_point},
            {"latitude": 51.50940214, "longitude": -0.133012},
        )

    async def test_reverse_with_language(self):
        result = await self.reverse_run(
            {"query": self.london_point, "language": "fr"},
            {}
        )
        assert "Royaume-Uni" in result.address

        result = await self.reverse_run(
            {"query": self.london_point, "language": "en"},
            {}
        )
        assert "United Kingdom" in result.address

    async def test_reverse_with_cc_format(self):
        result = await self.reverse_run(
            {"query": self.london_point, "cc_format": "alpha3"},
            {}
        )
        country_component = [comp for comp in result.raw["address_components"] if
                             'country' in comp['types']][0]
        assert country_component.get('short_name') == "GBR"

        result = await self.reverse_run(
            {"query": self.london_point, "cc_format": "alpha2"},
            {}
        )
        country_component = [comp for comp in result.raw["address_components"] if
                             'country' in comp['types']][0]
        assert country_component.get('short_name') == "GB"

    async def test_reverse_limit(self):
        result = await self.reverse_run(
            {
                "query": self.london_point,
                "limit": 5,
                "exactly_one": False
            },
            {}
        )
        assert len(result) == 5

    async def test_geocode_empty_result(self):
        with pytest.raises(exc.GeocoderQueryError):
            await self.geocode_run(
                {"query": ''},
                {},
                expect_failure=True,
            )
