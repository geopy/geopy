import json
import os
from abc import ABC, abstractmethod
from unittest.mock import ANY, patch

import pytest
from async_generator import async_generator, asynccontextmanager, yield_

from geopy import exc
from geopy.adapters import BaseAsyncAdapter
from geopy.location import Location

_env = {}
try:
    with open(".test_keys") as fp:
        _env.update(json.loads(fp.read()))
except IOError:
    _env.update(os.environ)


class SkipIfMissingEnv(dict):
    def __init__(self, env):
        super().__init__(env)
        self.is_internet_access_allowed = None

    def __getitem__(self, key):
        assert self.is_internet_access_allowed is not None
        if key not in self:
            if self.is_internet_access_allowed:
                pytest.skip("Missing geocoder credential: %s" % (key,))
            else:
                # Generate some dummy token. We won't perform a networking
                # request anyways.
                return "dummy"
        return super().__getitem__(key)


env = SkipIfMissingEnv(_env)


class BaseTestGeocoder(ABC):
    """
    Base for geocoder-specific test cases.
    """

    geocoder = None
    delta = 0.5

    @pytest.fixture(scope='class', autouse=True)
    @async_generator
    async def class_geocoder(_, request, patch_adapter, is_internet_access_allowed):
        """Prepare a class-level Geocoder instance."""
        cls = request.cls
        env.is_internet_access_allowed = is_internet_access_allowed

        geocoder = cls.make_geocoder()
        cls.geocoder = geocoder

        run_async = isinstance(geocoder.adapter, BaseAsyncAdapter)
        if run_async:
            async with geocoder:
                await yield_(geocoder)
        else:
            await yield_(geocoder)

    @classmethod
    @asynccontextmanager
    @async_generator
    async def inject_geocoder(cls, geocoder):
        """An async context manager allowing to inject a custom
        geocoder instance in a single test method which will
        be used by the `geocode_run`/`reverse_run` methods.
        """
        with patch.object(cls, 'geocoder', geocoder):
            run_async = isinstance(geocoder.adapter, BaseAsyncAdapter)
            if run_async:
                async with geocoder:
                    await yield_(geocoder)
            else:
                await yield_(geocoder)

    @pytest.fixture(autouse=True)
    def ensure_no_geocoder_assignment(self):
        yield
        assert self.geocoder is type(self).geocoder, (
            "Detected `self.geocoder` assignment. "
            "Please use `async with inject_geocoder(my_geocoder):` "
            "instead, which supports async adapters."
        )

    @classmethod
    @abstractmethod
    def make_geocoder(cls, **kwargs):  # pragma: no cover
        pass

    async def geocode_run(
        self, payload, expected, expect_failure=False,
        skiptest_on_failure=False
    ):
        """
        Calls geocoder.geocode(**payload), then checks against `expected`.
        """
        cls = type(self)
        result = await self._make_request(self.geocoder, 'geocode', **payload)
        if result is None:
            if expect_failure:
                return
            elif skiptest_on_failure:
                pytest.skip('%s: Skipping test due to empty result' % cls.__name__)
            else:
                pytest.fail('%s: No result found' % cls.__name__)
        if result == []:
            pytest.fail('%s returned an empty list instead of None' % cls.__name__)
        self._verify_request(result, exactly_one=payload.get('exactly_one', True),
                             **expected)
        return result

    async def reverse_run(
        self, payload, expected, expect_failure=False,
        skiptest_on_failure=False
    ):
        """
        Calls geocoder.reverse(**payload), then checks against `expected`.
        """
        cls = type(self)
        result = await self._make_request(self.geocoder, 'reverse', **payload)
        if result is None:
            if expect_failure:
                return
            elif skiptest_on_failure:
                pytest.skip('%s: Skipping test due to empty result' % cls.__name__)
            else:
                pytest.fail('%s: No result found' % cls.__name__)
        if result == []:
            pytest.fail('%s returned an empty list instead of None' % cls.__name__)
        self._verify_request(result, exactly_one=payload.get('exactly_one', True),
                             **expected)
        return result

    async def reverse_timezone_run(self, payload, expected):
        timezone = await self._make_request(
            self.geocoder, 'reverse_timezone', **payload)
        if expected is None:
            assert timezone is None
        else:
            assert timezone.pytz_timezone == expected

        return timezone

    async def _make_request(self, geocoder, method, *args, **kwargs):
        cls = type(self)
        call = getattr(geocoder, method)
        run_async = isinstance(geocoder.adapter, BaseAsyncAdapter)
        try:
            if run_async:
                result = await call(*args, **kwargs)
            else:
                result = call(*args, **kwargs)
        except exc.GeocoderQuotaExceeded:
            pytest.skip("%s: Quota exceeded" % cls.__name__)
        except exc.GeocoderTimedOut:
            pytest.skip("%s: Service timed out" % cls.__name__)
        except exc.GeocoderUnavailable:
            pytest.skip("%s: Service unavailable" % cls.__name__)
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
