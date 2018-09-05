
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
        'AZURE_SUBSCRIPTION_KEY',
        'BING_KEY',
        'GEONAMES_USERNAME',
        'LIVESTREETS_AUTH_ID',
        'LIVESTREETS_AUTH_TOKEN',
        'GEOCODEEARTH_KEY',
        'GEOCODEFARM_KEY',
        'HERE_APP_ID',
        'HERE_APP_CODE',
        'GEOCODEFARM_SKIP',
        'BAIDU_KEY',
        'BAIDU_KEY_REQUIRES_SK',
        'BAIDU_SEC_KEY',
        'MAPBOX_KEY',
        'OPENCAGE_KEY',
        'OPENMAPQUEST_APIKEY',
        'PELIAS_DOMAIN',
        'PELIAS_KEY',
        'PICKPOINT_KEY',
        'TOMTOM_KEY',
        'WHAT3WORDS_KEY',
        'IGNFRANCE_KEY',
        'IGNFRANCE_USERNAME',
        'IGNFRANCE_PASSWORD',
        'IGNFRANCE_REFERER',
        'YANDEX_KEY',
    )
    env = {key: os.environ.get(key, None) for key in keys}


EMPTY = object()


class GeocoderTestBase(unittest.TestCase):
    """
    Base for geocoder-specific test cases.
    """

    geocoder = None
    delta = 0.5

    def tearDown(self):
        # Typically geocoder instance is created in the setUpClass
        # method and is assigned to the TestCase as a class attribute.
        #
        # Individual test methods might assign a custom instance of
        # geocoder to the `self.geocoder` instance attribute, which
        # will shadow the class's `geocoder` attribute, used by
        # the `geocode_run`/`reverse_run` methods.
        #
        # The code below cleans up the possibly assigned instance
        # attribute.
        try:
            del self.geocoder
        except AttributeError:
            pass

    def geocode_run(self, payload, expected, expect_failure=False,
                    skiptest_on_failure=False):
        """
        Calls geocoder.geocode(**payload), then checks against `expected`.
        """
        result = self._make_request(self.geocoder.geocode, **payload)
        if result is None:
            cls = type(self)
            if expect_failure:
                return
            elif skiptest_on_failure:
                self.skipTest('%s: Skipping test due to empty result' % cls.__name__)
            else:
                self.fail('%s: No result found' % cls.__name__)
        self._verify_request(result, exactly_one=payload.get('exactly_one', True),
                             **expected)
        return result

    def reverse_run(self, payload, expected, expect_failure=False,
                    skiptest_on_failure=False):
        """
        Calls geocoder.reverse(**payload), then checks against `expected`.
        """
        result = self._make_request(self.geocoder.reverse, **payload)
        if result is None:
            cls = type(self)
            if expect_failure:
                return
            elif skiptest_on_failure:
                self.skipTest('%s: Skipping test due to empty result' % cls.__name__)
            else:
                self.fail('%s: No result found' % cls.__name__)
        self._verify_request(result, exactly_one=payload.get('exactly_one', True),
                             **expected)
        return result

    @classmethod
    def _make_request(cls, call, *args, **kwargs):
        """
        Handles remote service errors.
        """
        try:
            result = call(*args, **kwargs)
        except exc.GeocoderQuotaExceeded:
            raise unittest.SkipTest("%s: Quota exceeded" % cls.__name__)
        except exc.GeocoderTimedOut:
            raise unittest.SkipTest("%s: Service timed out" % cls.__name__)
        except exc.GeocoderUnavailable:
            raise unittest.SkipTest("%s: Service unavailable" % cls.__name__)
        return result

    def _verify_request(
            self,
            result,
            latitude=EMPTY,
            longitude=EMPTY,
            address=EMPTY,
            exactly_one=True,
            delta=None,
    ):
        """
        Verifies that result matches the kwargs given.
        """
        item = result if exactly_one else result[0]
        delta = delta or self.delta
        exceptions = []

        if latitude is not EMPTY:
            try:
                self.assertAlmostEqual(
                    item.latitude, latitude, delta=delta,
                    msg="latitude differs",
                )
            except AssertionError as e:
                exceptions.append(e)
        if longitude is not EMPTY:
            try:
                self.assertAlmostEqual(
                    item.longitude, longitude, delta=delta,
                    msg="longitude differs",
                )
            except AssertionError as e:
                exceptions.append(e)
        if address is not EMPTY:
            try:
                self.assertEqual(item.address, address,
                                 msg="address differs")
            except AssertionError as e:
                exceptions.append(e)

        self.assertFalse(exceptions)
