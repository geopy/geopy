import unittest

import pytest

from geopy.compat import u
from geopy.exc import GeocoderAuthenticationFailure
from geopy.geocoders import Baidu, BaiduV3
from geopy.point import Point
from test.geocoders.util import GeocoderTestBase, env


class BaiduTestCaseUnitTest(GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Baidu(
            api_key='DUMMYKEY1234',
            user_agent='my_user_agent/1.0'
        )

    def test_user_agent_custom(self):
        assert self.geocoder.headers['User-Agent'] == 'my_user_agent/1.0'


class BaiduQueriesTestCaseMixin:

    def test_basic_address(self):
        self.geocode_run(
            {"query": u(
                "\u5317\u4eac\u5e02\u6d77\u6dc0\u533a"
                "\u4e2d\u5173\u6751\u5927\u885727\u53f7"
            )},
            {"latitude": 39.983615544507, "longitude": 116.32295155093},
        )

    def test_reverse_point(self):
        self.reverse_run(
            {"query": Point(39.983615544507, 116.32295155093)},
            {"latitude": 39.983615544507, "longitude": 116.32295155093},
        )
        self.reverse_run(
            {"query": Point(39.983615544507, 116.32295155093), "exactly_one": False},
            {"latitude": 39.983615544507, "longitude": 116.32295155093},
        )


@unittest.skipUnless(
    bool(env.get('BAIDU_KEY')),
    "No BAIDU_KEY env variable set"
)
class BaiduTestCase(BaiduQueriesTestCaseMixin, GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Baidu(
            api_key=env['BAIDU_KEY'],
            timeout=3,
        )

    def test_invalid_ak(self):
        self.geocoder = Baidu(api_key='DUMMYKEY1234')
        with pytest.raises(GeocoderAuthenticationFailure) as exc_info:
            self.geocode_run({"query": u("baidu")}, None)
        assert str(exc_info.value) == 'Invalid AK'


@unittest.skipUnless(
    bool(env.get('BAIDU_KEY_REQUIRES_SK')) and bool(env.get('BAIDU_SEC_KEY')),
    "BAIDU_KEY_REQUIRES_SK and BAIDU_SEC_KEY env variables not set"
)
class BaiduSKTestCase(BaiduQueriesTestCaseMixin, GeocoderTestBase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = Baidu(
            api_key=env['BAIDU_KEY_REQUIRES_SK'],
            security_key=env['BAIDU_SEC_KEY'],
            timeout=3,
        )

    def test_sn_with_peculiar_chars(self):
        self.geocode_run(
            {"query": u(
                "\u5317\u4eac\u5e02\u6d77\u6dc0\u533a"
                "\u4e2d\u5173\u6751\u5927\u885727\u53f7"
                " ' & = , ? %"
            )},
            {"latitude": 39.983615544507, "longitude": 116.32295155093},
        )


@unittest.skipUnless(
    bool(env.get('BAIDU_V3_KEY')),
    "No BAIDU_V3_KEY env variable set"
)
class BaiduV3TestCase(BaiduTestCase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = BaiduV3(
            api_key=env['BAIDU_V3_KEY'],
            timeout=3,
        )


@unittest.skipUnless(
    bool(env.get('BAIDU_V3_KEY_REQUIRES_SK')) and bool(env.get('BAIDU_V3_SEC_KEY')),
    "BAIDU_V3_KEY_REQUIRES_SK and BAIDU_V3_SEC_KEY env variables not set"
)
class BaiduV3SKTestCase(BaiduSKTestCase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = BaiduV3(
            api_key=env['BAIDU_V3_KEY_REQUIRES_SK'],
            security_key=env['BAIDU_V3_SEC_KEY'],
            timeout=3,
        )
