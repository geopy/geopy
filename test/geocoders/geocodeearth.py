import unittest

from geopy.geocoders import GeocodeEarth
from test.geocoders.pelias import BasePeliasTestCase
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(
    bool(env['GEOCODEEARTH_KEY']),
    "No GEOCODEEARTH_KEY env variable set"
)
class GeocodeEarthTestCase(BasePeliasTestCase, GeocoderTestBase):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return GeocodeEarth(env['GEOCODEEARTH_KEY'],
                            **kwargs)
