from geopy.compat import u
from geopy.exc import GeocoderQueryError
from geopy.geocoders import DataBC
from test.geocoders.util import GeocoderTestBase


class DataBCTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = DataBC()

    def test_user_agent_custom(self):
        geocoder = DataBC(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_geocode(self):
        """
        DataBC.geocode
        """
        self.geocode_run(
            {"query": "135 North Pym Road, Parksville"},
            {"latitude": 49.321, "longitude": -124.337},
        )

    def test_unicode_name(self):
        """
        DataBC.geocode unicode
        """
        self.geocode_run(
            {"query": u("Barri\u00e8re")},
            {"latitude": 51.179, "longitude": -120.123},
        )

    def test_multiple_results(self):
        """
        DataBC.geocode with multiple results
        """
        res = self.geocode_run(
            {"query": "1st St", "exactly_one": False},
            {},
        )
        self.assertGreater(len(res), 1)

    def test_optional_params(self):
        """
        DataBC.geocode using optional params
        """

        self.geocode_run(
            {"query": "5670 malibu terrace nanaimo bc",
             "location_descriptor": "accessPoint",
             "set_back": 100},
            {"latitude": 49.2299, "longitude": -124.0163},
        )

    def test_query_error(self):
        """
        DataBC.geocode with bad query parameters
        """
        with self.assertRaises(GeocoderQueryError):
            self.geocode_run(
                {"query": "1 Main St, Vancouver",
                 "location_descriptor": "access_Point"},
                {},
                expect_failure=True,
            )
