import unittest

from geopy.compat import u
from geopy.point import Point
from geopy.geocoders import PickPoint
from test.geocoders.util import GeocoderTestBase, env

@unittest.skipUnless(bool(env['PICKPOINT_KEY']),
                     "No PICKPOINT_KEY env variable set"
)
class PickPointTestCase(GeocoderTestBase):

    delta = 0.04

    @classmethod
    def setUpClass(cls):
        print('HERE')
        cls.geocoder = PickPoint(api_key=env['PICKPOINT_KEY'])

    def test_geocode(self):
        """
        PickPoint.geocode
        """
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        """
        PickPoint.geocode unicode
        """
        self.geocode_run(
            {"query": u("\u6545\u5bab")},
            {"latitude": 39.916, "longitude": 116.390},
        )

    def test_reverse_string(self):
        """
        PickPoint.reverse string
        """
        self.reverse_run(
            {"query": "40.75376406311989, -73.98489005863667"},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667}
        )

    def test_reverse_point(self):
        """
        PickPoint.reverse Point
        """
        self.reverse_run(
            {"query": Point(40.75376406311989, -73.98489005863667)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667}
        )

    def test_city_district_with_dict_query(self):
        """
        PickPoint.geocode using `addressdetails`
        """
        geocoder = PickPoint(api_key=self.API_KEY, country_bias='DE')
        query = {'postalcode': 10117}
        result = self._make_request(
            geocoder.geocode,
            query,
            addressdetails=True,

        )
        self.assertEqual(result.raw['address']['city_district'], 'Mitte')

    def test_geocode_language_parameter(self):
        """
        PickPoint.geocode using `language`
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
        PickPoint.reverse using `language`
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
        PickPoint.geocode with full geometry (response in WKT format)
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
        PickPoint.geocode with full geometry (response in svg format)
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
        PickPoint.geocode with full geometry (response in kml format)
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
        PickPoint.geocode with full geometry (response in geojson format)
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
