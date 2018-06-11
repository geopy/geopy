from geopy.geocoders import Nominatim
from test.geocoders.nominatim_base import BaseNominatimTestCase
from test.geocoders.util import GeocoderTestBase


class NominatimTestCase(BaseNominatimTestCase, GeocoderTestBase):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return Nominatim(**kwargs)
