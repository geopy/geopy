import unittest

import pytest

from geopy.exc import ConfigurationError
from geopy.geocoders import OpenMapQuest
from test.geocoders.nominatim import BaseNominatimTestCase
from test.geocoders.util import GeocoderTestBase, env


class OpenMapQuestNoNetTestCase(GeocoderTestBase):

    def test_user_agent_custom(self):
        geocoder = OpenMapQuest(
            api_key='DUMMYKEY1234',
            user_agent='my_user_agent/1.0'
        )
        assert geocoder.headers['User-Agent'] == 'my_user_agent/1.0'

    def test_raises_without_apikey(self):
        with pytest.raises(ConfigurationError):
            OpenMapQuest()


@unittest.skipUnless(
    bool(env.get('OPENMAPQUEST_APIKEY')),
    "No OPENMAPQUEST_APIKEY env variable set"
)
class OpenMapQuestTestCase(BaseNominatimTestCase, GeocoderTestBase):

    @classmethod
    def make_geocoder(cls, **kwargs):
        return OpenMapQuest(api_key=env['OPENMAPQUEST_APIKEY'],
                            timeout=3, **kwargs)
