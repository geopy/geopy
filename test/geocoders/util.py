
import os
import json
import unittest
from collections import defaultdict

from geopy import exc

env = defaultdict(lambda: None)
try:
    with open(".test_keys") as fp:
        env.update(json.loads(fp.read()))
except IOError:
    env.update(os.environ)


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
