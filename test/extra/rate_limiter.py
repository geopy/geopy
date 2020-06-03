from unittest.mock import MagicMock, patch, sentinel

import pytest

from geopy.exc import GeocoderQuotaExceeded, GeocoderServiceError
from geopy.extra.rate_limiter import RateLimiter


@pytest.fixture
def mock_clock():
    with patch.object(RateLimiter, '_clock') as mock_clock:
        yield mock_clock


@pytest.fixture
def mock_sleep():
    with patch.object(RateLimiter, '_sleep') as mock_sleep:
        yield mock_sleep


def test_min_delay(mock_clock, mock_sleep):
    min_delay = 3.5
    mock_func = MagicMock()

    mock_clock.side_effect = [1]
    rl = RateLimiter(mock_func, min_delay_seconds=min_delay)

    # First call -- no delay
    clock_first = 10
    mock_clock.side_effect = [clock_first, clock_first]  # no delay here
    rl(sentinel.arg, kwa=sentinel.kwa)
    mock_sleep.assert_not_called()
    mock_func.assert_called_once_with(sentinel.arg, kwa=sentinel.kwa)

    # Second call after min_delay/3 seconds -- should be delayed
    clock_second = clock_first + (min_delay / 3)
    mock_clock.side_effect = [clock_second, clock_first + min_delay]
    rl(sentinel.arg, kwa=sentinel.kwa)
    mock_sleep.assert_called_with(min_delay - (clock_second - clock_first))
    mock_sleep.reset_mock()

    # Third call after min_delay*2 seconds -- no delay again
    clock_third = clock_first + min_delay + min_delay * 2
    mock_clock.side_effect = [clock_third, clock_third]
    rl(sentinel.arg, kwa=sentinel.kwa)
    mock_sleep.assert_not_called()


def test_max_retries(mock_clock, mock_sleep):
    mock_func = MagicMock()
    mock_clock.return_value = 1
    rl = RateLimiter(mock_func, max_retries=3,
                     return_value_on_exception=sentinel.return_value)

    # Non-geopy errors must not be swallowed
    mock_func.side_effect = ValueError
    with pytest.raises(ValueError):
        rl(sentinel.arg)
    assert 1 == mock_func.call_count
    mock_func.reset_mock()

    # geopy errors must be swallowed and retried
    mock_func.side_effect = GeocoderServiceError
    assert sentinel.return_value == rl(sentinel.arg)
    assert 4 == mock_func.call_count
    mock_func.reset_mock()

    # Successful value must be returned
    mock_func.side_effect = [
        GeocoderServiceError, GeocoderServiceError, sentinel.good
    ]
    assert sentinel.good == rl(sentinel.arg)
    assert 3 == mock_func.call_count
    mock_func.reset_mock()

    # When swallowing is disabled, the exception must be raised
    rl.swallow_exceptions = False
    mock_func.side_effect = GeocoderQuotaExceeded
    with pytest.raises(GeocoderQuotaExceeded):
        rl(sentinel.arg)
    assert 4 == mock_func.call_count
    mock_func.reset_mock()


def test_error_wait_seconds(mock_clock, mock_sleep):
    mock_func = MagicMock()
    error_wait = 3.3

    mock_clock.return_value = 1
    rl = RateLimiter(mock_func, max_retries=3,
                     error_wait_seconds=error_wait,
                     return_value_on_exception=sentinel.return_value)

    mock_func.side_effect = GeocoderServiceError
    assert sentinel.return_value == rl(sentinel.arg)
    assert 4 == mock_func.call_count
    assert 3 == mock_sleep.call_count
    mock_sleep.assert_called_with(error_wait)
    mock_func.reset_mock()
