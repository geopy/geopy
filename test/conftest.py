import atexit
import contextlib
import os
from collections import defaultdict
from functools import partial
from statistics import mean, median
from time import sleep
from timeit import default_timer
from unittest.mock import patch
from urllib.parse import urlparse

import pytest

import geopy.geocoders
from geopy.adapters import AdapterHTTPError, BaseAdapter, BaseSyncAdapter
from geopy.geocoders.base import _DEFAULT_ADAPTER_CLASS

max_retries = int(os.getenv('GEOPY_TEST_RETRIES', 2))
error_wait_seconds = float(os.getenv('GEOPY_TEST_ERROR_WAIT_SECONDS', 3))
no_retries_for_hosts = set(os.getenv('GEOPY_TEST_NO_RETRIES_FOR_HOSTS', '').split(','))
retry_status_codes = (429,)


def pytest_addoption(parser):
    # This option will probably be used in downstream packages,
    # thus it should be considered a public interface.
    parser.addoption(
        "--skip-tests-requiring-internet",
        action="store_true",
        help="Skip tests requiring Internet access.",
    )


@pytest.fixture(scope='session')
def is_internet_access_allowed(request):
    return not request.config.getoption("--skip-tests-requiring-internet")


@pytest.fixture
def skip_if_internet_access_is_not_allowed(is_internet_access_allowed):
    # Used in test_adapters.py, which doesn't use the injected adapter below.
    if not is_internet_access_allowed:
        pytest.skip("Skipping a test requiring Internet access")


def netloc_from_url(url):
    return urlparse(url).netloc


def pretty_dict_format(heading, dict_to_format,
                       item_prefix='  ', legend='',
                       value_mapper=lambda v: v):
    s = [heading]
    if not dict_to_format:
        s.append(item_prefix + '-- empty --')
    else:
        max_key_len = max(len(k) for k in dict_to_format.keys())
        for k, v in sorted(dict_to_format.items()):
            s.append('%s%s%s' % (item_prefix, k.ljust(max_key_len + 2),
                                 value_mapper(v)))
        if legend:
            s.append('')
            s.append('* %s' % legend)
    s.append('')  # trailing newline
    return '\n'.join(s)


class RequestsMonitor:
    """RequestsMonitor holds statistics of Adapter requests."""

    def __init__(self):
        self.host_stats = defaultdict(lambda: dict(count=0, retries=0, times=[]))

    def record_request(self, url):
        hostname = netloc_from_url(url)
        self.host_stats[hostname]['count'] += 1

    def record_retry(self, url):
        hostname = netloc_from_url(url)
        self.host_stats[hostname]['retries'] += 1

    @contextlib.contextmanager
    def record_response(self, url):
        start = default_timer()
        try:
            yield
        finally:
            end = default_timer()
            hostname = netloc_from_url(url)
            self.host_stats[hostname]['times'].append(end - start)

    def __str__(self):
        def value_mapper(v):
            tv = v['times']
            times_format = (
                "min:%5.2fs, median:%5.2fs, max:%5.2fs, mean:%5.2fs, total:%5.2fs"
            )
            if tv:
                # min/max require a non-empty sequence.
                times = times_format % (min(tv), median(tv), max(tv), mean(tv), sum(tv))
            else:
                nan = float("nan")
                times = times_format % (nan, nan, nan, nan, 0)

            count = "count:%3d" % v['count']
            retries = "retries:%3d" % v['retries'] if v['retries'] else ""
            return "; ".join(s for s in (count, times, retries) if s)

        legend = (
            "count – number of requests (excluding retries); "
            "min, median, max, mean, total – request duration statistics "
            "(excluding failed requests); retries – number of retries."
        )
        return pretty_dict_format('Request statistics per hostname',
                                  self.host_stats,
                                  legend=legend,
                                  value_mapper=value_mapper)


@pytest.fixture(scope='session')
def requests_monitor():
    return RequestsMonitor()


@pytest.fixture(autouse=True, scope='session')
def print_requests_monitor_report(requests_monitor):
    yield

    def report():
        print(str(requests_monitor))

    # https://github.com/pytest-dev/pytest/issues/2704
    # https://stackoverflow.com/a/38806934
    atexit.register(report)


@pytest.fixture(autouse=True, scope='session')
def patch_adapter(requests_monitor, is_internet_access_allowed):
    """
    Patch the default Adapter to provide the following features:
        - Retry failed requests. Makes test runs more stable.
        - Track statistics with RequestsMonitor.
        - Skip tests requiring Internet access when Internet access is not allowed.
    """

    class AdapterProxy(BaseAdapter):
        def __init__(self, *, proxies, ssl_context, adapter_factory):
            self.adapter = adapter_factory(
                proxies=proxies,
                ssl_context=ssl_context,
            )

        def get_json(self, url, *, timeout, headers):
            return self._wrapped_get(
                url,
                partial(self.adapter.get_json, url, timeout=timeout, headers=headers),
            )

        def get_text(self, url, *, timeout, headers):
            return self._wrapped_get(
                url,
                partial(self.adapter.get_text, url, timeout=timeout, headers=headers),
            )

        def _wrapped_get(self, url, do_request):
            if not is_internet_access_allowed:
                # Assume that *all* geocoders require Internet access
                pytest.skip("Skipping a test requiring Internet access")

            requests_monitor.record_request(url)

            netloc = netloc_from_url(url)
            retries = max_retries

            if netloc in no_retries_for_hosts:
                retries = 0

            for i in range(retries + 1):
                try:
                    with requests_monitor.record_response(url):
                        resp = do_request()
                except AdapterHTTPError as error:
                    if i == retries or error.status_code not in retry_status_codes:
                        # Note: we shouldn't blindly retry on any >=400 code,
                        # because some of them are actually expected in tests
                        # (like input validation verification).

                        # TODO Retry failures with the 200 code?
                        # Some geocoders return failures with 200 code
                        # (like GoogleV3 for Quota Exceeded).
                        # Should we detect this somehow to restart such requests?
                        #
                        # Re-raise -- don't retry this request
                        raise
                    else:
                        # Swallow the error and retry the request
                        pass
                except Exception:
                    if i == retries:
                        raise
                else:
                    return resp

                requests_monitor.record_retry(url)
                sleep(error_wait_seconds)
            raise RuntimeError("Should not have been reached")

    # In order to take advantage of Keep-Alives in tests, the actual Adapter
    # should be persisted between the test runs, so this fixture must be
    # in the "session" scope.
    InjectableProxy.inject(partial(AdapterProxy, adapter_factory=_DEFAULT_ADAPTER_CLASS))
    yield
    InjectableProxy.inject(None)


class InjectableProxy:
    _cls_factory = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._target_factory = None
        self._target = None

    @classmethod
    def inject(cls, factory):
        cls._cls_factory = factory

    @property
    def target(self):
        cls = type(self)
        if self._target is None or self._target_factory is not cls._cls_factory:
            self._target = cls._cls_factory(**self.kwargs)
            self._target_factory = cls._cls_factory
        return self._target

    def __getattr__(self, name):
        return getattr(self.target, name)


BaseSyncAdapter.register(InjectableProxy)


# InjectableProxy allows to substitute an Adapter instance for already
# created geocoder classes. Geocoder testcases tend to create Geocoders
# in the unittest's `setUpClass` method, so the geocoder instances
# could be reused between test runs.
#
# Unfortunately `setUpClass` is executed before the fixtures, so we cannot
# just patch `geopy.geocoders.options` in a fixture. This hack with
# `InjectableProxy` allows to inject an Adapter from a pytest fixture.
patch.object(geopy.geocoders.options, "default_adapter_factory", InjectableProxy).start()
