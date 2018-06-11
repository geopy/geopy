from abc import ABCMeta, abstractmethod
from mock import patch
from six import with_metaclass

import geopy.geocoders
from geopy.compat import u
from geopy.point import Point


class BaseNominatimTestCase(with_metaclass(ABCMeta, object)):
    # Common test cases for Nominatim-based geocoders.

    delta = 0.04

    @classmethod
    @abstractmethod
    def make_geocoder(cls, **kwargs):
        pass

    @classmethod
    def setUpClass(cls):
        cls.geocoder = cls.make_geocoder()

    def test_geocode(self):
        self.geocode_run(
            {"query": "435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_unicode_name(self):
        self.geocode_run(
            {"query": u("\u6545\u5bab \u5317\u4eac")},
            {"latitude": 39.916, "longitude": 116.390},
        )

    @patch.object(geopy.geocoders.options, 'default_user_agent',
                  'mocked_user_agent/0.0.0')
    def test_user_agent_default(self):
        geocoder = self.make_geocoder()
        self.assertEqual(geocoder.headers['User-Agent'],
                         'mocked_user_agent/0.0.0')

    def test_user_agent_custom(self):
        geocoder = self.make_geocoder(
            user_agent='my_user_agent/1.0'
        )
        self.assertEqual(geocoder.headers['User-Agent'], 'my_user_agent/1.0')

    def test_reverse_string(self):
        location = self.reverse_run(
            {"query": "40.75376406311989, -73.98489005863667"},
            {"latitude": 40.753, "longitude": -73.984}
        )
        self.assertIn("New York", location.address)

    def test_reverse_point(self):
        location = self.reverse_run(
            {"query": Point(40.75376406311989, -73.98489005863667)},
            {"latitude": 40.753, "longitude": -73.984}
        )
        self.assertIn("New York", location.address)

    def test_city_district_with_dict_query(self):
        self.geocoder = self.make_geocoder(country_bias='DE')
        query = {'postalcode': 10117}
        result = self.geocode_run(
            {"query": query, "addressdetails": True},
            {},
        )
        self.assertEqual(result.raw['address']['city_district'], 'Mitte')

    def test_geocode_language_parameter(self):
        query = "Mohrenstrasse Berlin"
        result_geocode = self.geocode_run(
            {"query": query, "addressdetails": True,
             "language": "de"},
            {},
        )
        self.assertEqual(
            result_geocode.raw['address']['country'],
            "Deutschland"
        )
        result_geocode = self.geocode_run(
            {"query": query, "addressdetails": True,
             "language": "en"},
            {},
        )
        self.assertEqual(
            result_geocode.raw['address']['country'],
            "Germany"
        )

    def test_reverse_language_parameter(self):
        query = "52.51693903613385, 13.3859332733135"
        result_reverse_de = self.reverse_run(
            {"query": query, "exactly_one": True, "language": "de"},
            {},
        )
        self.assertEqual(
            result_reverse_de.raw['address']['country'],
            "Deutschland"
        )

        result_reverse_en = self.reverse_run(
            {"query": query, "exactly_one": True, "language": "en"},
            {},
        )
        self.assertTrue(
            # have had a change in the exact authority name
            "Germany" in result_reverse_en.raw['address']['country']
        )

    def test_geocode_geometry_wkt(self):
        result_geocode = self.geocode_run(
            {"query": "Halensee,Berlin", "geometry": 'WKT'},
            {},
        )
        self.assertEqual(
            result_geocode.raw['geotext'].startswith('POLYGON(('),
            True
        )

    def test_geocode_geometry_svg(self):
        result_geocode = self.geocode_run(
            {"query": "Halensee,Berlin", "geometry": 'svg'},
            {},
        )
        self.assertEqual(
            result_geocode.raw['svg'].startswith('M 13.'),
            True
        )

    def test_geocode_geometry_kml(self):
        result_geocode = self.geocode_run(
            {"query": "Halensee,Berlin", "geometry": 'kml'},
            {},
        )
        self.assertEqual(
            result_geocode.raw['geokml'].startswith('<Polygon>'),
            True
        )

    def test_geocode_geometry_geojson(self):
        """
        Nominatim.geocode with full geometry (response in geojson format)
        """
        result_geocode = self.geocode_run(
            {"query": "Halensee,Berlin", "geometry": 'geojson'},
            {},
        )
        self.assertEqual(
            result_geocode.raw['geojson'].get('type'),
            'Polygon'
        )

    def test_missing_reverse_details(self):
        query = (46.46131, 6.84311)
        res = self.reverse_run(
            {"query": query},
            {}
        )
        self.assertIn("address", res.raw)

        res = self.reverse_run(
            {"query": query, "addressdetails": False},
            {},
        )
        self.assertNotIn('address', res.raw)

    def test_view_box(self):
        res = self.geocode_run(
            {"query": "Maple Street"},
            {},
        )
        self.assertFalse(50 <= res.latitude <= 52)
        self.assertFalse(-0.15 <= res.longitude <= -0.11)

        for view_box in [(-0.11, 52, -0.15, 50),
                         [Point(52, -0.11), Point(50, -0.15)],
                         ("-0.11", "52", "-0.15", "50")]:
            self.geocoder = self.make_geocoder(view_box=view_box)
            self.geocode_run(
                {"query": "Maple Street"},
                {"latitude": 51.5223513, "longitude": -0.1382104}
            )
