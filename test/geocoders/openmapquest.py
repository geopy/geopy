from geopy.geocoders import OpenMapQuest
from test.geocoders.nominatim import BaseTestNominatim
from test.geocoders.util import env


class TestUnitOpenMapQuest:

    def test_user_agent_custom(self):
        geocoder = OpenMapQuest(
            api_key='DUMMYKEY1234',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'


class TestOpenMapQuest(BaseTestNominatim):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return OpenMapQuest(api_key=env['OPENMAPQUEST_APIKEY'],
                            timeout=3, **kwargs)
