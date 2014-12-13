
import unittest

from geopy.compat import u
from geopy.point import Point
from geopy.geocoders import Baidu
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(  # pylint: disable=R0904,C0111
    bool(env.get('BAIDU_KEY')),
    "No BAIDU_KEY env variable set"
)
class BaiduTestCase(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Baidu(
            scheme='http',
            api_key=env['BAIDU_KEY']
        )
        cls.delta_exact = 0.02

    def test_basic_address(self):
        """
        Baidu.geocode
        """
        self.geocode_run(
            {"query": u(
                "\u5317\u4eac\u5e02\u6d77\u6dc0\u533a"
                "\u4e2d\u5173\u6751\u5927\u885727\u53f7"
            )},
            {"latitude": 39.983615544507, "longitude": 116.32295155093},
        )

    def test_reverse_address(self):
        """
        Baidu.reverse address
        """
        self.reverse_run(
            {"query": u(
                "\u5317\u4eac\u5e02\u6d77\u6dc0\u533a\u4e2d"
                "\u5173\u6751\u5927\u885727\u53f7"
            )},
            {"latitude": 39.983615544507, "longitude": 116.32295155093},
        )

    def test_reverse_point(self):
        """
        Baidu.reverse Point
        """
        self.reverse_run(
            {"query": Point(39.983615544507, 116.32295155093)},
            {"latitude": 39.983615544507, "longitude": 116.32295155093},
        )
