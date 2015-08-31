from mock import patch
from geopy.compat import u
from geopy.point import Point
from geopy.geocoders import Nominatim
from test.geocoders.util import GeocoderTestBase


class NominatimTestCase(GeocoderTestBase): # pylint: disable=R0904,C0111

    delta = 0.04

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Nominatim()
        cls.known_state_de = "Verwaltungsregion Ionische Inseln"
        cls.known_state_en = "Ionian Islands Periphery"

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

    def test_user_agent_default(self):
        with patch('geopy.geocoders.base.DEFAULT_USER_AGENT', 'mocked_user_agent/0.0.0'):
            geocoder = Nominatim()
            self.assertEqual(geocoder.headers['User-Agent'], 'mocked_user_agent/0.0.0')

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
        result_geocode = self._make_request(
            self.geocoder.geocode,
            self.known_state_en,
            addressdetails=True,
            language="de",
        )
        self.assertEqual(
            result_geocode.raw['address']['state'],
            self.known_state_de
        )

    def test_reverse_language_parameter(self):
        """
        Nominatim.reverse using `language`
        """
        result_reverse_de = self._make_request(
            self.geocoder.reverse,
            "37.78250, 20.89506",
            exactly_one=True,
            language="de",
        )
        self.assertEqual(
            result_reverse_de.raw['address']['state'],
            self.known_state_de
        )

        result_reverse_en = self._make_request(
            self.geocoder.reverse,
            "37.78250, 20.89506",
            exactly_one=True,
            language="en"
        )
        self.assertTrue(
            # have had a change in the exact authority name
            "Ionian Islands" in result_reverse_en.raw['address']['state']
        )

    def test_geocode_geometry_wkt(self):
        """
        Nominatim.geocode with full geometry (response in WKT format)
        """
        result_geocode = self._make_request(
            self.geocoder.geocode,
            self.known_state_en,
            geometry='WKT',

        )
        self.assertEqual(
            result_geocode.raw['geotext'].startswith('MULTIPOLYGON((('),
            True
        )

    def test_geocode_geometry_svg(self):
        """
        Nominatim.geocode with full geometry (response in svg format)
        """
        result_geocode = self._make_request(
            self.geocoder.geocode,
            self.known_state_en,
            geometry='svg',

        )
        self.assertEqual(
            result_geocode.raw['svg'].startswith('M 19.'),
            True
        )

    def test_geocode_geometry_kml(self):
        """
        Nominatim.geocode with full geometry (response in kml format)
        """
        result_geocode = self._make_request(
            self.geocoder.geocode,
            self.known_state_en,
            geometry='kml',

        )
        self.assertEqual(
            result_geocode.raw['geokml'].startswith('<MultiGeometry>'),
            True
        )

    def test_geocode_geometry_geojson(self):
        """
        Nominatim.geocode with full geometry (response in geojson format)
        """
        result_geocode = self._make_request(
            self.geocoder.geocode,
            self.known_state_en,
            geometry='geojson',

        )
        self.assertEqual(
            result_geocode.raw['geojson'].get('type'),
            'MultiPolygon'
        )
