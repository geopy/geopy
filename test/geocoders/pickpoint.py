import warnings

from geopy.geocoders import PickPoint
from test.geocoders.nominatim import BaseTestNominatim
from test.geocoders.util import env


class TestPickPoint(BaseTestNominatim):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return PickPoint(api_key=env['PICKPOINT_KEY'],
                         timeout=3, **kwargs)

    async def test_no_nominatim_user_agent_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            PickPoint(api_key=env['PICKPOINT_KEY'])
            assert 0 == len(w)
