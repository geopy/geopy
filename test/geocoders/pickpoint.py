import unittest
import warnings

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

    def test_no_nominatim_user_agent_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            PickPoint(api_key=env['PICKPOINT_KEY'])
            self.assertEqual(0, len(w))
