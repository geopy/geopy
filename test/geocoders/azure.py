import unittest

from geopy.geocoders import AzureMaps
from test.geocoders.util import GeocoderTestBase, env
from test.geocoders.tomtom import BaseTomTomTestCase


@unittest.skipUnless(
    bool(env.get('AZURE_SUBSCRIPTION_KEY')),
    "No AZURE_SUBSCRIPTION_KEY env variable set"
)
class AzureMapsTestCase(BaseTomTomTestCase, GeocoderTestBase):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return AzureMaps(env['AZURE_SUBSCRIPTION_KEY'], timeout=3,
                         **kwargs)
