import pytest

from geopy.geocoders import AzureMaps
from test.geocoders.tomtom import BaseTestTomTom
from test.geocoders.util import env


@pytest.mark.skipif(
    not bool(env.get('AZURE_SUBSCRIPTION_KEY')),
    reason="No AZURE_SUBSCRIPTION_KEY env variable set"
)
class TestAzureMaps(BaseTestTomTom):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return AzureMaps(env['AZURE_SUBSCRIPTION_KEY'], timeout=3,
                         **kwargs)
