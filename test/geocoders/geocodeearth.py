import pytest

from geopy.geocoders import GeocodeEarth
from test.geocoders.pelias import BaseTestPelias
from test.geocoders.util import env


@pytest.mark.skipif(
    not bool(env['GEOCODEEARTH_KEY']),
    reason="No GEOCODEEARTH_KEY env variable set"
)
class TestGeocodeEarth(BaseTestPelias):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return GeocodeEarth(env['GEOCODEEARTH_KEY'],
                            **kwargs)
