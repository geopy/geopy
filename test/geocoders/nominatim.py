
from geopy.point import Point
from geopy.geocoders import Nominatim
from test.geocoders.util import GeocoderTestBase, CommonTestMixin

class NominatimTestCase(GeocoderTestBase, CommonTestMixin): # pylint: disable=R0904,C0111

    delta = 0.04

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Nominatim()
        cls.known_state_de = u"Verwaltungsregion Ionische Inseln"
        cls.known_state_en = u"Ionian Islands Periphery"

    # def test_reverse_address(self):
    #     """
    #     Nominatim.reverse address
    #     """
    #     self.reverse_run(
    #         {"query": (
    #             u"Jose Bonifacio de Andrada e Silva, 6th Avenue, Diamond "
    #             u"District, Hell's Kitchen, NYC, New York, 10020, "
    #             u"United States of America"
    #         )},
    #         {"latitude": 40.75376406311989, "longitude": -73.98489005863667}
    #     )

    def test_reverse_string(self):
        """
        Nominatim.reverse string
        """
        self.reverse_run(
            {"query": u"40.75376406311989, -73.98489005863667"},
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
        result = geocoder.geocode(query, addressdetails=True)
        self.assertEqual(result.raw['address']['city_district'], u'Mitte')

    def test_geocode_language_parameter(self):
        """
        Nominatim.geocode using `language`
        """
        result_geocode = self.geocoder.geocode(
            self.known_state_en,
            addressdetails=True,
            language="de"
        )
        self.assertEqual(
            result_geocode.raw['address']['state'],
            self.known_state_de
        )

    def test_reverse_language_parameter(self):
        """
        Nominatim.reverse using `language`
        """
        result_reverse_de = self.geocoder.reverse(
            "37.78250, 20.89506",
            exactly_one=True,
            language="de"
        )
        self.assertEqual(
            result_reverse_de.raw['address']['state'],
            self.known_state_de
        )

        result_reverse_en = self.geocoder.reverse(
            "37.78250, 20.89506",
            exactly_one=True,
            language="en"
        )
        self.assertEqual(
            result_reverse_en.raw['address']['state'],
            self.known_state_en
        )
