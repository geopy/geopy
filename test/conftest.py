import asyncio
import atexit
import contextlib
import importlib
import os
import types
from collections import defaultdict
from functools import partial
from statistics import mean, median
from time import sleep
from timeit import default_timer
from unittest.mock import patch
from urllib.parse import urlparse

import pytest

import geopy.geocoders
from geopy.adapters import AdapterHTTPError, BaseAsyncAdapter, BaseSyncAdapter
from geopy.geocoders.base import _DEFAULT_ADAPTER_CLASS


def load_adapter_cls(adapter_ref):
    actual_adapter_class = _DEFAULT_ADAPTER_CLASS
    if adapter_ref:
        module_s, cls_s = adapter_ref.rsplit(".", 1)
        module = importlib.import_module(module_s)
        actual_adapter_class = getattr(module, cls_s)
    return actual_adapter_class


max_retries = int(os.getenv('GEOPY_TEST_RETRIES', 2))
error_wait_seconds = float(os.getenv('GEOPY_TEST_ERROR_WAIT_SECONDS', 3))
no_retries_for_hosts = set(os.getenv('GEOPY_TEST_NO_RETRIES_FOR_HOSTS', '').split(','))
default_adapter = load_adapter_cls(os.getenv('GEOPY_TEST_ADAPTER'))
default_adapter_is_async = issubclass(default_adapter, BaseAsyncAdapter)
retry_status_codes = (
    403,  # Forbidden (probably due to a rate limit)
    429,  # Too Many Requests (definitely a rate limit)
    502,  # Bad Gateway
)


def pytest_report_header(config):
    internet_access = "allowed" if _is_internet_access_allowed(config) else "disabled"
    adapter_type = "async" if default_adapter_is_async else "sync"
    return (
        "geopy:\n"
        "    internet access: %s\n"
        "    adapter: %r\n"
        "    adapter type: %s"
        % (internet_access, default_adapter, adapter_type)
    )


def pytest_addoption(parser):
    # This option will probably be used in downstream packages,
    # thus it should be considered a public interface.
    parser.addoption(
        "--skip-tests-requiring-internet",
        action="store_true",
        help="Skip tests requiring Internet access.",
    )


def _is_internet_access_allowed(config):
    return not config.getoption("--skip-tests-requiring-internet")


@pytest.fixture(scope='session')
def is_internet_access_allowed(request):
    return _is_internet_access_allowed(request.config)


@pytest.fixture
def skip_if_internet_access_is_not_allowed(is_internet_access_allowed):
    # Used in test_adapters.py, which doesn't use the injected adapter below.
    if not is_internet_access_allowed:
        pytest.skip("Skipping a test requiring Internet access")


@pytest.fixture(autouse=True, scope="session")
def event_loop():
    # Geocoder instances have class scope, so the event loop
    # should have session scope.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


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


@pytest.fixture(scope='session')
def retries_enabled_session():
    return types.SimpleNamespace(value=True)


@pytest.fixture
def disable_adapter_retries(retries_enabled_session):
    retries_enabled_session.value = False
    yield
    retries_enabled_session.value = True


@pytest.fixture(autouse=True, scope='session')
def patch_adapter(
    requests_monitor, retries_enabled_session, is_internet_access_allowed
):
    """
    Patch the default Adapter to provide the following features:
        - Retry failed requests. Makes test runs more stable.
        - Track statistics with RequestsMonitor.
        - Skip tests requiring Internet access when Internet access is not allowed.
    """

    if default_adapter_is_async:

        class AdapterProxy(BaseAdapterProxy, BaseAsyncAdapter):
            async def __aenter__(self):
                assert await self.adapter.__aenter__() is self.adapter
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return await self.adapter.__aexit__(exc_type, exc_val, exc_tb)

            async def _wrapped_get(self, url, do_request):
                res = None
                gen = self._retries(url)
                while True:
                    try:
                        next(gen)
                    except StopIteration:
                        break
                    assert res is None
                    try:
                        res = await do_request()
                    except Exception as e:
                        error_wait_seconds = gen.throw(e)
                        await asyncio.sleep(error_wait_seconds)
                    else:
                        assert gen.send(res) is None
                assert res is not None
                return res

    else:

        class AdapterProxy(BaseAdapterProxy, BaseSyncAdapter):
            def _wrapped_get(self, url, do_request):
                res = None
                gen = self._retries(url)
                while True:
                    try:
                        next(gen)
                    except StopIteration:
                        break
                    assert res is None
                    try:
                        res = do_request()
                    except Exception as e:
                        error_wait_seconds = gen.throw(e)
                        sleep(error_wait_seconds)
                    else:
                        assert gen.send(res) is None
                assert res is not None
                return res

    # In order to take advantage of Keep-Alives in tests, the actual Adapter
    # should be persisted between the test runs, so this fixture must be
    # in the "session" scope.
    adapter_factory = partial(
        AdapterProxy,
        adapter_factory=default_adapter,
        requests_monitor=requests_monitor,
        retries_enabled_session=retries_enabled_session,
        is_internet_access_allowed=is_internet_access_allowed,
    )
    with patch.object(
        geopy.geocoders.options, "default_adapter_factory", adapter_factory
    ):
        yield


class BaseAdapterProxy:
    def __init__(
        self,
        *,
        proxies,
        ssl_context,
        adapter_factory,
        requests_monitor,
        retries_enabled_session,
        is_internet_access_allowed
    ):
        self.adapter = adapter_factory(
            proxies=proxies,
            ssl_context=ssl_context,
        )
        self.requests_monitor = requests_monitor
        self.retries_enabled_session = retries_enabled_session
        self.is_internet_access_allowed = is_internet_access_allowed

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

    def _retries(self, url):
        if not self.is_internet_access_allowed:
            # Assume that *all* geocoders require Internet access
            pytest.skip("Skipping a test requiring Internet access")

        self.requests_monitor.record_request(url)

        netloc = netloc_from_url(url)
        retries = max_retries

        if netloc in no_retries_for_hosts:
            retries = 0

        for i in range(retries + 1):
            try:
                with self.requests_monitor.record_response(url):
                    yield
            except AdapterHTTPError as error:
                if not self.retries_enabled_session.value:
                    raise

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
                yield None
                return

            self.requests_monitor.record_retry(url)
            yield error_wait_seconds
        raise RuntimeError("Should not have been reached")
