from mock import patch

import geopy.geocoders
from geopy.compat import u
from geopy.geocoders import Nominatim
from geopy.point import Point
from test.geocoders.util import GeocoderTestBase


class NominatimTestCase(GeocoderTestBase):

    delta = 0.04

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Nominatim()

    def tearDown(self):
        try:
            del self.geocoder
        except AttributeError:
            pass

    def test_geocode(self):
        """
        Nominatim.geocode
        """
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        """
        Nominatim.geocode unicode
        """
        self.geocode_run(
            {"query": u("\u6545\u5bab")},
            {"latitude": 39.916, "longitude": 116.390},
        )

    @patch.object(geopy.geocoders.options, 'default_user_agent',
                  'mocked_user_agent/0.0.0')
    def test_user_agent_default(self):
        geocoder = Nominatim()
        self.assertEqual(geocoder.headers['User-Agent'],
                         'mocked_user_agent/0.0.0')

    def test_user_agent_custom(self):
        geocoder = Nominatim(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_reverse_string(self):
        """
        Nominatim.reverse string
        """
        self.reverse_run(
            {"query": "40.75376406311989, -73.98489005863667"},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667}
        )

    def test_reverse_point(self):
        """
        Nominatim.reverse Point
        """
        self.reverse_run(
            {"query": Point(40.75376406311989, -73.98489005863667)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667}
        )

    def test_city_district_with_dict_query(self):
        """
        Nominatim.geocode using `addressdetails`
        """
        geocoder = Nominatim(country_bias='DE')
        query = {'postalcode': 10117}
        result = self._make_request(
            geocoder.geocode,
            query,
            addressdetails=True,

        )
        self.assertEqual(result.raw['address']['city_district'], 'Mitte')

    def test_geocode_language_parameter(self):
        """
        Nominatim.geocode using `language`
        """
        input = "Mohrenstrasse Berlin"
        result_geocode = self._make_request(
            self.geocoder.geocode,
            input,
            addressdetails=True,
            language="de",
        )
        self.assertEqual(
            result_geocode.raw['address']['country'],
            "Deutschland"
        )
        result_geocode = self._make_request(
            self.geocoder.geocode,
            input,
            addressdetails=True,
            language="en",
        )
        self.assertEqual(
            result_geocode.raw['address']['country'],
            "Germany"
        )

    def test_reverse_language_parameter(self):
        """
        Nominatim.reverse using `language`
        """
        result_reverse_de = self._make_request(
            self.geocoder.reverse,
            "52.51693903613385, 13.3859332733135",
            exactly_one=True,
            language="de",
        )
        self.assertEqual(
            result_reverse_de.raw['address']['country'],
            "Deutschland"
        )

        result_reverse_en = self._make_request(
            self.geocoder.reverse,
            "52.51693903613385, 13.3859332733135",
            exactly_one=True,
            language="en"
        )
        self.assertTrue(
            # have had a change in the exact authority name
            "Germany" in result_reverse_en.raw['address']['country']
        )

    def test_geocode_geometry_wkt(self):
        """
        Nominatim.geocode with full geometry (response in WKT format)
        """
        input = "Halensee,Berlin"
        result_geocode = self._make_request(
            self.geocoder.geocode,
            input,
            geometry='WKT',

        )
        self.assertEqual(
            result_geocode.raw['geotext'].startswith('POLYGON(('),
            True
        )

    def test_geocode_geometry_svg(self):
        """
        Nominatim.geocode with full geometry (response in svg format)
        """
        input = "Halensee,Berlin"
        result_geocode = self._make_request(
            self.geocoder.geocode,
            input,
            geometry='svg',

        )
        self.assertEqual(
            result_geocode.raw['svg'].startswith('M 13.'),
            True
        )

    def test_geocode_geometry_kml(self):
        """
        Nominatim.geocode with full geometry (response in kml format)
        """
        input = "Halensee,Berlin"
        result_geocode = self._make_request(
            self.geocoder.geocode,
            input,
            geometry='kml',

        )
        self.assertEqual(
            result_geocode.raw['geokml'].startswith('<Polygon>'),
            True
        )

    def test_geocode_geometry_geojson(self):
        """
        Nominatim.geocode with full geometry (response in geojson format)
        """
        input = "Halensee,Berlin"
        result_geocode = self._make_request(
            self.geocoder.geocode,
            input,
            geometry='geojson',

        )
        self.assertEqual(
            result_geocode.raw['geojson'].get('type'),
            'Polygon'
        )

    def test_missing_reverse_details(self):
        """
        Nominatim.reverse without address details
        """
        res = self._make_request(
            self.geocoder.reverse,
            query=(46.46131, 6.84311),
            addressdetails=False
        )
        self.assertNotIn(
            'address',
            res
        )

    def test_view_box(self):
        self.geocode_run(
            {"query": "Maple Street"},
            {"latitude": 36.809551, "longitude": -97.050604},
        )
        for view_box in [(-0.11, 52, -0.15, 50),
                         [Point(52, -0.11), Point(50, -0.15)],
                         ("-0.11", "52", "-0.15", "50")]:
            self.geocoder = Nominatim(view_box=view_box)
            self.geocode_run(
                {"query": "Maple Street"},
                {"latitude": 51.5223513, "longitude": -0.1382104}
            )
