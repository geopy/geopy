import unittest
try:
    from contextlib import ExitStack
except ImportError:
    # python 2
    from contextlib2 import ExitStack

from mock import patch, MagicMock, sentinel

from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderServiceError, GeocoderQuotaExceeded


class RateLimiterTestCase(unittest.TestCase):

    def setUp(self):
        self._stack = ExitStack()
        self.mock_clock = self._stack.enter_context(
            patch.object(RateLimiter, '_clock'))
        self.mock_sleep = self._stack.enter_context(
            patch.object(RateLimiter, '_sleep'))
        self.mock_func = MagicMock()

    def tearDown(self):
        self._stack.close()

    def test_min_delay(self):
        min_delay = 3.5

        self.mock_clock.side_effect = [1]
        rl = RateLimiter(self.mock_func, min_delay_seconds=min_delay)

        # First call -- no delay
        clock_first = 10
        self.mock_clock.side_effect = [clock_first, clock_first]  # no delay here
        rl(sentinel.arg, kwa=sentinel.kwa)
        self.mock_sleep.assert_not_called()
        self.mock_func.assert_called_once_with(sentinel.arg, kwa=sentinel.kwa)

        # Second call after min_delay/3 seconds -- should be delayed
        clock_second = clock_first + (min_delay / 3)
        self.mock_clock.side_effect = [clock_second, clock_first + min_delay]
        rl(sentinel.arg, kwa=sentinel.kwa)
        self.mock_sleep.assert_called_with(min_delay - (clock_second - clock_first))
        self.mock_sleep.reset_mock()

        # Third call after min_delay*2 seconds -- no delay again
        clock_third = clock_first + min_delay + min_delay * 2
        self.mock_clock.side_effect = [clock_third, clock_third]
        rl(sentinel.arg, kwa=sentinel.kwa)
        self.mock_sleep.assert_not_called()

    def test_max_retries(self):
        self.mock_clock.return_value = 1
        rl = RateLimiter(self.mock_func, max_retries=3,
                         return_value_on_exception=sentinel.return_value)

        # Non-geopy errors must not be swallowed
        self.mock_func.side_effect = ValueError
        with self.assertRaises(ValueError):
            rl(sentinel.arg)
        self.assertEqual(1, self.mock_func.call_count)
        self.mock_func.reset_mock()

        # geopy errors must be swallowed and retried
        self.mock_func.side_effect = GeocoderServiceError
        self.assertEqual(sentinel.return_value, rl(sentinel.arg))
        self.assertEqual(4, self.mock_func.call_count)
        self.mock_func.reset_mock()

        # Successful value must be returned
        self.mock_func.side_effect = [
            GeocoderServiceError, GeocoderServiceError, sentinel.good
        ]
        self.assertEqual(sentinel.good, rl(sentinel.arg))
        self.assertEqual(3, self.mock_func.call_count)
        self.mock_func.reset_mock()

        # When swallowing is disabled, the exception must be raised
        rl.swallow_exceptions = False
        self.mock_func.side_effect = GeocoderQuotaExceeded
        with self.assertRaises(GeocoderQuotaExceeded):
            rl(sentinel.arg)
        self.assertEqual(4, self.mock_func.call_count)
        self.mock_func.reset_mock()

    def test_error_wait_seconds(self):
        error_wait = 3.3

        self.mock_clock.return_value = 1
        rl = RateLimiter(self.mock_func, max_retries=3,
                         error_wait_seconds=error_wait,
                         return_value_on_exception=sentinel.return_value)

        self.mock_func.side_effect = GeocoderServiceError
        self.assertEqual(sentinel.return_value, rl(sentinel.arg))
        self.assertEqual(4, self.mock_func.call_count)
        self.assertEqual(3, self.mock_sleep.call_count)
        self.mock_sleep.assert_called_with(error_wait)
        self.mock_func.reset_mock()
