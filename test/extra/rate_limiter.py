import asyncio
from unittest.mock import MagicMock, patch, sentinel

import pytest

from geopy.exc import GeocoderQuotaExceeded, GeocoderServiceError
from geopy.extra.rate_limiter import AsyncRateLimiter, RateLimiter


@pytest.fixture(params=[False, True])
def is_async(request):
    return request.param


@pytest.fixture
def auto_async(is_async):
    if is_async:
        async def auto_async(coro):
            return await coro
    else:
        async def auto_async(result):
            return result
    return auto_async


@pytest.fixture
def auto_async_side_effect(is_async):
    def auto_async_side_effect(side_effect):
        if not is_async:
            return side_effect

        mock = MagicMock(side_effect=side_effect)

        async def func(*args, **kwargs):
            return mock(*args, **kwargs)

        return func

    return auto_async_side_effect


@pytest.fixture
def rate_limiter_cls(is_async):
    if is_async:
        return AsyncRateLimiter
    else:
        return RateLimiter


@pytest.fixture
def mock_clock(rate_limiter_cls):
    with patch.object(rate_limiter_cls, '_clock') as mock_clock:
        yield mock_clock


@pytest.fixture
def mock_sleep(auto_async_side_effect, rate_limiter_cls):
    with patch.object(rate_limiter_cls, '_sleep') as mock_sleep:
        mock_sleep.side_effect = auto_async_side_effect(None)
        yield mock_sleep


async def test_min_delay(
    rate_limiter_cls, mock_clock, mock_sleep, auto_async_side_effect, auto_async
):
    mock_func = MagicMock()
    mock_func.side_effect = auto_async_side_effect(None)
    min_delay = 3.5

    mock_clock.side_effect = [1]
    rl = rate_limiter_cls(mock_func, min_delay_seconds=min_delay)

    # First call -- no delay
    clock_first = 10
    mock_clock.side_effect = [clock_first, clock_first]  # no delay here
    await auto_async(rl(sentinel.arg, kwa=sentinel.kwa))
    mock_sleep.assert_not_called()
    mock_func.assert_called_once_with(sentinel.arg, kwa=sentinel.kwa)

    # Second call after min_delay/3 seconds -- should be delayed
    clock_second = clock_first + (min_delay / 3)
    mock_clock.side_effect = [clock_second, clock_first + min_delay]
    await auto_async(rl(sentinel.arg, kwa=sentinel.kwa))
    mock_sleep.assert_called_with(min_delay - (clock_second - clock_first))
    mock_sleep.reset_mock()

    # Third call after min_delay*2 seconds -- no delay again
    clock_third = clock_first + min_delay + min_delay * 2
    mock_clock.side_effect = [clock_third, clock_third]
    await auto_async(rl(sentinel.arg, kwa=sentinel.kwa))
    mock_sleep.assert_not_called()


async def test_max_retries(
    rate_limiter_cls, mock_clock, mock_sleep, auto_async_side_effect, auto_async
):
    mock_func = MagicMock()
    mock_clock.return_value = 1
    rl = rate_limiter_cls(
        mock_func, max_retries=3,
        return_value_on_exception=sentinel.return_value,
    )

    # Non-geopy errors must not be swallowed
    mock_func.side_effect = auto_async_side_effect(ValueError)
    with pytest.raises(ValueError):
        await auto_async(rl(sentinel.arg))
    assert 1 == mock_func.call_count
    mock_func.reset_mock()

    # geopy errors must be swallowed and retried
    mock_func.side_effect = auto_async_side_effect(GeocoderServiceError)
    assert sentinel.return_value == await auto_async(rl(sentinel.arg))
    assert 4 == mock_func.call_count
    mock_func.reset_mock()

    # Successful value must be returned
    mock_func.side_effect = auto_async_side_effect(side_effect=[
        GeocoderServiceError, GeocoderServiceError, sentinel.good
    ])
    assert sentinel.good == await auto_async(rl(sentinel.arg))
    assert 3 == mock_func.call_count
    mock_func.reset_mock()

    # When swallowing is disabled, the exception must be raised
    rl.swallow_exceptions = False
    mock_func.side_effect = auto_async_side_effect(GeocoderQuotaExceeded)
    with pytest.raises(GeocoderQuotaExceeded):
        await auto_async(rl(sentinel.arg))
    assert 4 == mock_func.call_count
    mock_func.reset_mock()


async def test_error_wait_seconds(
    rate_limiter_cls, mock_clock, mock_sleep, auto_async_side_effect, auto_async
):
    mock_func = MagicMock()
    error_wait = 3.3

    mock_clock.return_value = 1
    rl = rate_limiter_cls(
        mock_func, max_retries=3,
        error_wait_seconds=error_wait,
        return_value_on_exception=sentinel.return_value,
    )

    mock_func.side_effect = auto_async_side_effect(GeocoderServiceError)
    assert sentinel.return_value == await auto_async(rl(sentinel.arg))
    assert 4 == mock_func.call_count
    assert 3 == mock_sleep.call_count
    mock_sleep.assert_called_with(error_wait)
    mock_func.reset_mock()


async def test_sync_raises_for_awaitable():
    def g():  # non-async function returning an awaitable -- like `geocode`.
        async def coro():
            pass  # pragma: no cover

        # Make a task from the coroutine, to avoid
        # the `coroutine 'coro' was never awaited` warning:
        task = asyncio.ensure_future(coro())
        return task

    rl = RateLimiter(g)

    with pytest.raises(ValueError):
        await rl()
