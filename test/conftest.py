# coding: utf-8
import atexit
import os
from collections import defaultdict
from statistics import mean
from time import sleep
from timeit import default_timer

import pytest
import six
from six.moves.urllib.parse import urlparse

max_retries = int(os.getenv('GEOPY_TEST_RETRIES', 2))
error_wait_seconds = float(os.getenv('GEOPY_TEST_ERROR_WAIT_SECONDS', 3))
no_retries_for_hosts = set(os.getenv('GEOPY_TEST_NO_RETRIES_FOR_HOSTS', '').split(','))
retry_status_codes = (429,)

if six.PY3:
    http_handler_do_open = 'urllib.request.HTTPHandler.do_open'
    https_handler_do_open = 'urllib.request.HTTPSHandler.do_open'
    from urllib.request import HTTPHandler, HTTPSHandler
else:
    http_handler_do_open = 'urllib2.HTTPHandler.do_open'
    https_handler_do_open = 'urllib2.HTTPSHandler.do_open'
    from urllib2 import HTTPHandler, HTTPSHandler


def netloc_from_req(req):  # urllib request
    return urlparse(req.get_full_url()).netloc


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


class RequestsMonitor(object):
    """RequestsMonitor holds statistics of urllib requests."""

    def __init__(self):
        self.host_stats = defaultdict(lambda: dict(count=0, retries=0, times=[]))

    def record_request(self, req):
        hostname = netloc_from_req(req)
        self.host_stats[hostname]['count'] += 1

    def record_retry(self, req):
        hostname = netloc_from_req(req)
        self.host_stats[hostname]['retries'] += 1

    def record_response(self, req, resp, seconds_elapsed):
        hostname = netloc_from_req(req)
        self.host_stats[hostname]['times'].append(seconds_elapsed)

    def __str__(self):
        def value_mapper(v):
            tv = v['times']
            times_format = "min:%5.2fs, max:%5.2fs, mean:%5.2fs, total:%5.2fs"
            if tv:
                # min/max require a non-empty sequence.
                times = times_format % (min(tv), max(tv), mean(tv), sum(tv))
            else:
                nan = float("nan")
                times = times_format % (nan, nan, nan, 0)

            count = "count:%3d" % v['count']
            retries = "retries:%3d" % v['retries'] if v['retries'] else ""
            return "; ".join(s for s in (count, times, retries) if s)

        legend = (
            "count – number of requests (excluding retries); "
            "min, max, mean, total – request duration statistics "
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


@pytest.fixture(autouse=True)
def patch_urllib(monkeypatch, requests_monitor):
    """
    Patch urllib to provide the following features:
        - Retry failed requests. Makes test runs more stable.
        - Track statistics with RequestsMonitor.

    Retries could have been implemented differently:
        - In test.geocoders.util.GeocoderTestBase._make_request. The issue
          is that proxy tests use raw urlopen on the proxy server side,
          which will not be covered by _make_request.
        - With pytest plugins, such as pytest-rerunfailures. This
          might be a good alternative, however, they don't distinguish
          between network and test logic failures (the latter shouldn't
          be re-run).
    """

    def mock_factory(do_open):
        def wrapped_do_open(self, conn, req, *args, **kwargs):
            requests_monitor.record_request(req)

            retries = max_retries
            netloc = netloc_from_req(req)
            is_proxied = req.host != netloc

            if is_proxied or netloc in no_retries_for_hosts:
                # XXX If there's a system proxy enabled, the failed requests
                # won't be retried at all because of this check.
                # We need to disable retries for proxies in order to
                # not retry requests to the local proxy server set up in
                # tests/proxy_server.py, which breaks request counters
                # in tests/test_proxy.py.
                # Perhaps we could also check that `req.host` points
                # to localhost?
                retries = 0

            for i in range(retries + 1):
                try:
                    start = default_timer()
                    resp = do_open(self, conn, req, *args, **kwargs)
                    end = default_timer()

                    if i == retries or resp.getcode() not in retry_status_codes:
                        # Note: we shouldn't blindly retry on any >=400 code,
                        # because some of them are actually expected in tests
                        # (like input validation verification).

                        # TODO Retry failures with the 200 code?
                        # Some geocoders return failures with 200 code
                        # (like GoogleV3 for Quota Exceeded).
                        # Should we detect this somehow to restart such requests?
                        requests_monitor.record_response(req, resp, end - start)
                        return resp
                except:  # noqa
                    if i == retries:
                        raise
                requests_monitor.record_retry(req)
                sleep(error_wait_seconds)
            raise RuntimeError("Should not have been reached")

        return wrapped_do_open

    original_http_do_open = HTTPHandler.do_open
    original_https_do_open = HTTPSHandler.do_open
    monkeypatch.setattr(http_handler_do_open, mock_factory(original_http_do_open))
    monkeypatch.setattr(https_handler_do_open, mock_factory(original_https_do_open))
