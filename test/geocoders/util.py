
import os
import json
import unittest
from collections import defaultdict

from geopy import exc

try:
    env = defaultdict(lambda: None)
    with open(".test_keys") as fp:
        env.update(json.loads(fp.read()))
except IOError:
    keys = (
        'ARCGIS_USERNAME',
        'ARCGIS_PASSWORD',
        'ARCGIS_REFERER',
        'YAHOO_KEY',
        'YAHOO_SECRET',
        'BING_KEY',
        'MAPQUEST_KEY',
        'GEONAMES_USERNAME',
        'LIVESTREETS_AUTH_ID',
        'LIVESTREETS_AUTH_TOKEN',
        'GEOCODERDOTUS_USERNAME',
        'GEOCODERDOTUS_PASSWORD',
        'GEOCODEFARM_KEY',
        'BAIDU_KEY',
        'OPENCAGE_KEY',
        'WHAT3WORDS_KEY',
        'IGNFRANCE_KEY',
        'IGNFRANCE_USERNAME',
        'IGNFRANCE_PASSWORD',
        'IGNFRANCE_REFERER',
        'GEOCLIENT_APP_ID',
        'GEOCLIENT_APP_KEY',
    )
    env = {key: os.environ.get(key, None) for key in keys}


class Empty(object):  # pylint: disable=R0903
    """
    Non-None NULL.
    """
    pass


EMPTY = Empty()


class GeocoderTestBase(unittest.TestCase): # pylint: disable=R0904
    """
    Base for geocoder-specific test cases.
    """

    geocoder = None
    delta = 0.5

    def geocode_run(self, payload, expected, expect_failure=False):
        """
        Calls geocoder.geocode(**payload), then checks against `expected`.
        """
        result = self._make_request(self.geocoder.geocode, **payload)
        if result is None:
            if not expect_failure:
                self.fail('No result found')
            else:
                return
        self._verify_request(result, **expected)

    def reverse_run(self, payload, expected, expect_failure=False):
        """
        Calls geocoder.reverse(**payload), then checks against `expected`.
        """
        result = self._make_request(self.geocoder.reverse, **payload)
        if result is None:
            if not expect_failure:
                self.fail('No result found')
            else:
                return
        self._verify_request(result, **expected)

    @staticmethod
    def _make_request(call, *args, **kwargs):
        """
        Handles remote service errors.
        """
        try:
            result = call(*args, **kwargs)
        except exc.GeocoderQuotaExceeded:
            raise unittest.SkipTest("Quota exceeded")
        except exc.GeocoderTimedOut:
            raise unittest.SkipTest("Service timed out")
        except exc.GeocoderUnavailable:
            raise unittest.SkipTest("Service unavailable")
        return result

    def _verify_request(
            self,
            result,
            raw=EMPTY,
            latitude=EMPTY,
            longitude=EMPTY,
            address=EMPTY
        ):
        """
        Verifies that a a result matches the kwargs given.
        """
        item = result[0] if isinstance(result, (tuple, list)) else result

        if raw != EMPTY:
            self.assertEqual(item.raw, raw)
        if latitude != EMPTY:
            self.assertAlmostEqual(
                item.latitude, latitude, delta=self.delta
            )
        if longitude != EMPTY:
            self.assertAlmostEqual(
                item.longitude, longitude, delta=self.delta
            )
        if address != EMPTY:
            self.assertEqual(
                item.address, address
            )
