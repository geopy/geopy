import unittest

from geopy.geocoders import PickPoint
from test.geocoders.nominatim import BaseNominatimTestCase
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(
    bool(env['PICKPOINT_KEY']),
    "No PICKPOINT_KEY env variable set"
)
class PickPointTestCase(BaseNominatimTestCase, GeocoderTestBase):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return PickPoint(api_key=env['PICKPOINT_KEY'],
                         timeout=3, **kwargs)
