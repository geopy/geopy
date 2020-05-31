
import json
import os
import unittest
from collections import defaultdict

import pytest
from mock import ANY

from geopy import exc
from geopy.location import Location

env = defaultdict(lambda: None)
try:
    with open(".test_keys") as fp:
        env.update(json.loads(fp.read()))
except IOError:
    env.update(os.environ)


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
        cls = type(self)
        result = self._make_request(self.geocoder.geocode, **payload)
        if result is None:
            if expect_failure:
                return
            elif skiptest_on_failure:
                self.skipTest('%s: Skipping test due to empty result' % cls.__name__)
            else:
                self.fail('%s: No result found' % cls.__name__)
        if result == []:
            self.fail('%s returned an empty list instead of None' % cls.__name__)
        self._verify_request(result, exactly_one=payload.get('exactly_one', True),
                             **expected)
        return result

    def reverse_run(self, payload, expected, expect_failure=False,
                    skiptest_on_failure=False):
        """
        Calls geocoder.reverse(**payload), then checks against `expected`.
        """
        cls = type(self)
        result = self._make_request(self.geocoder.reverse, **payload)
        if result is None:
            if expect_failure:
                return
            elif skiptest_on_failure:
                self.skipTest('%s: Skipping test due to empty result' % cls.__name__)
            else:
                self.fail('%s: No result found' % cls.__name__)
        if result == []:
            self.fail('%s returned an empty list instead of None' % cls.__name__)
        self._verify_request(result, exactly_one=payload.get('exactly_one', True),
                             **expected)
        return result

    @classmethod
    def _make_request(cls, call, *args, **kwargs):
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
            latitude=ANY,
            longitude=ANY,
            address=ANY,
            exactly_one=True,
            delta=None,
    ):
        if exactly_one:
            assert isinstance(result, Location)
        else:
            assert isinstance(result, list)

        item = result if exactly_one else result[0]
        delta = delta or self.delta

        expected = (
            pytest.approx(latitude, abs=delta) if latitude is not ANY else ANY,
            pytest.approx(longitude, abs=delta) if longitude is not ANY else ANY,
            address,
        )
        received = (
            item.latitude,
            item.longitude,
            item.address,
        )
        assert received == expected
