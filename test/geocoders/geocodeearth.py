from geopy.geocoders import GeocodeEarth
from test.geocoders.pelias import BaseTestPelias
from test.geocoders.util import env


class TestGeocodeEarth(BaseTestPelias):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return GeocodeEarth(env['GEOCODEEARTH_KEY'],
                            **kwargs)
