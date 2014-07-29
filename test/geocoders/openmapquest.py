
from geopy.geocoders import OpenMapQuest
from test.geocoders.util import GeocoderTestBase, CommonTestMixin


class OpenMapQuestTestCase(GeocoderTestBase, CommonTestMixin): # pylint: disable=R0904,C0111

    @classmethod
    def setUpClass(cls):
        cls.geocoder = OpenMapQuest(scheme='http', timeout=3)
        cls.delta = 0.04
