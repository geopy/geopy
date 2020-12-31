""":class:`.RateLimiter` and :class:`.AsyncRateLimiter` allow to perform bulk
operations while gracefully handling error responses and adding delays
when needed.

In the example below a delay of 1 second (``min_delay_seconds=1``)
will be added between each pair of ``geolocator.geocode`` calls; all
:class:`geopy.exc.GeocoderServiceError` exceptions will be retried
(up to ``max_retries`` times)::

    import pandas as pd
    df = pd.DataFrame({'name': ['paris', 'berlin', 'london']})

    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="specify_your_app_name_here")

    from geopy.extra.rate_limiter import RateLimiter
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    df['location'] = df['name'].apply(geocode)

    df['point'] = df['location'].apply(lambda loc: tuple(loc.point) if loc else None)

This would produce the following DataFrame::

    >>> df
         name                                           location  \\
    0   paris  (Paris, Île-de-France, France métropolitaine, ...
    1  berlin  (Berlin, 10117, Deutschland, (52.5170365, 13.3...
    2  london  (London, Greater London, England, SW1A 2DU, UK...

                               point
    0   (48.8566101, 2.3514992, 0.0)
    1  (52.5170365, 13.3888599, 0.0)
    2  (51.5073219, -0.1276474, 0.0)

To pass extra options to the `geocode` call::

    from functools import partial
    df['location'] = df['name'].apply(partial(geocode, language='de'))

To see a progress bar::

    from tqdm import tqdm
    tqdm.pandas()
    df['location'] = df['name'].progress_apply(geocode)

Before using rate limiting classes, please consult with the Geocoding
service ToS, which might explicitly consider bulk requests (even throttled)
a violation.
"""

import asyncio
import inspect
import threading
from itertools import chain, count
from time import sleep
from timeit import default_timer

from geopy.exc import GeocoderServiceError
from geopy.util import logger

__all__ = ("AsyncRateLimiter", "RateLimiter")


def _is_last_gen(count):
    """list(_is_last_gen(2)) -> [False, False, True]"""
    return chain((False for _ in range(count)), [True])


class BaseRateLimiter:
    """Base Rate Limiter class for both sync and async versions."""

    _retry_exceptions = (GeocoderServiceError,)

    def __init__(
        self,
        *,
        min_delay_seconds,
        max_retries,
        swallow_exceptions,
        return_value_on_exception
    ):
        self.min_delay_seconds = min_delay_seconds
        self.max_retries = max_retries
        self.swallow_exceptions = swallow_exceptions
        self.return_value_on_exception = return_value_on_exception
        assert max_retries >= 0

        # State:
        self._lock = threading.Lock()
        self._last_call = None

    def _clock(self):  # pragma: no cover
        return default_timer()

    def _acquire_request_slot_gen(self):
        # Requests rate is limited by `min_delay_seconds` interval.
        #
        # Imagine the time axis as a grid with `min_delay_seconds` step,
        # where we would call each step as a "request slot". RateLimiter
        # guarantees that each "request slot" contains at most 1 request.
        #
        # Note that actual requests might take longer time than
        # `min_delay_seconds`. In that case you might want to consider
        # parallelizing requests (with a ThreadPool for sync mode and
        # asyncio tasks for async), to keep the requests rate closer
        # to `min_delay_seconds`.
        #
        # This generator thread-safely acquires a "request slot", and
        # if it fails to do that at this time, it yields the amount
        # of seconds to sleep until the next attempt. The generator
        # stops only when the "request slot" has been successfully
        # acquired.
        #
        # There's no ordering between the concurrent requests. The first
        # request to acquire the lock wins the next "request slot".
        while True:
            with self._lock:
                clock = self._clock()
                if self._last_call is None:
                    # A first iteration -- start immediately.
                    self._last_call = clock
                    return
                seconds_since_last_call = clock - self._last_call
                wait = self.min_delay_seconds - seconds_since_last_call
                if wait <= 0:
                    # A successfully acquired request slot.
                    self._last_call = clock
                    return
            # Couldn't acquire a request slot. Wait until the beginning
            # of the next slot to try again.
            yield wait

    def _retries_gen(self, args, kwargs):
        for i, is_last_try in zip(count(), _is_last_gen(self.max_retries)):
            try:
                yield i  # Run the function.
            except self._retry_exceptions:
                if is_last_try:
                    yield True  # The exception should be raised
                else:
                    logger.warning(
                        type(self).__name__ + " caught an error, retrying "
                        "(%s/%s tries). Called with (*%r, **%r).",
                        i,
                        self.max_retries,
                        args,
                        kwargs,
                        exc_info=True,
                    )
                    yield False  # The exception has been swallowed.
                    continue
            else:
                # A successful run -- stop retrying:
                return  # pragma: no cover

    def _handle_exc(self, args, kwargs):
        if self.swallow_exceptions:
            logger.warning(
                type(self).__name__ + " swallowed an error after %r retries. "
                "Called with (*%r, **%r).",
                self.max_retries,
                args,
                kwargs,
                exc_info=True,
            )
            return self.return_value_on_exception
        else:
            raise


class RateLimiter(BaseRateLimiter):
    """This is a Rate Limiter implementation for synchronous functions
    (like geocoders with the default :class:`geopy.adapters.BaseSyncAdapter`).

    Examples::

        from geopy.extra.rate_limiter import RateLimiter
        from geopy.geocoders import Nominatim

        geolocator = Nominatim(user_agent="specify_your_app_name_here")

        search = ["moscow", "paris", "berlin", "tokyo", "beijing"]
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
        locations = [geocode(s) for s in search]

        search = [
            (55.47, 37.32), (48.85, 2.35), (52.51, 13.38),
            (34.69, 139.40), (39.90, 116.39)
        ]
        reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)
        locations = [reverse(s) for s in search]

    RateLimiter class is thread-safe. If geocoding service's responses
    are slower than `min_delay_seconds`, then you can benefit from
    parallelizing the work::

        import concurrent.futures

        geolocator = OpenMapQuest(api_key="...")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1/20)

        with concurrent.futures.ThreadPoolExecutor() as e:
            locations = list(e.map(geocode, search))

    .. versionchanged:: 2.0
       Added thread-safety support.
    """

    def __init__(
        self,
        func,
        *,
        min_delay_seconds=0.0,
        max_retries=2,
        error_wait_seconds=5.0,
        swallow_exceptions=True,
        return_value_on_exception=None
    ):
        """
        :param callable func:
            A function which should be wrapped by the rate limiter.

        :param float min_delay_seconds:
            Minimum delay in seconds between the wrapped ``func`` calls.
            To convert :abbr:`RPS (Requests Per Second)` rate to
            ``min_delay_seconds`` you need to divide 1 by RPS. For example,
            if you need to keep the rate at 20 RPS, you can use
            ``min_delay_seconds=1/20``.

        :param int max_retries:
            Number of retries on exceptions. Only
            :class:`geopy.exc.GeocoderServiceError` exceptions are
            retried -- others are always re-raised. ``max_retries + 1``
            requests would be performed at max per query. Set
            ``max_retries=0`` to disable retries.

        :param float error_wait_seconds:
            Time to wait between retries after errors. Must be
            greater or equal to ``min_delay_seconds``.

        :param bool swallow_exceptions:
            Should an exception be swallowed after retries? If not,
            it will be re-raised. If yes, the ``return_value_on_exception``
            will be returned.

        :param return_value_on_exception:
            Value to return on failure when ``swallow_exceptions=True``.

        """
        super().__init__(
            min_delay_seconds=min_delay_seconds,
            max_retries=max_retries,
            swallow_exceptions=swallow_exceptions,
            return_value_on_exception=return_value_on_exception,
        )
        self.func = func
        self.error_wait_seconds = error_wait_seconds
        assert error_wait_seconds >= min_delay_seconds
        assert max_retries >= 0

    def _sleep(self, seconds):  # pragma: no cover
        logger.debug(type(self).__name__ + " sleep(%r)", seconds)
        sleep(seconds)

    def _acquire_request_slot(self):
        for wait in self._acquire_request_slot_gen():
            self._sleep(wait)

    def __call__(self, *args, **kwargs):
        gen = self._retries_gen(args, kwargs)
        for _ in gen:
            self._acquire_request_slot()
            try:
                res = self.func(*args, **kwargs)
                if inspect.isawaitable(res):
                    raise ValueError(
                        "An async awaitable has been passed to `RateLimiter`. "
                        "Use `AsyncRateLimiter` instead, which supports awaitables."
                    )
                return res
            except self._retry_exceptions as e:
                if gen.throw(e):
                    # A final try
                    return self._handle_exc(args, kwargs)
                self._sleep(self.error_wait_seconds)

        raise RuntimeError("Should not have been reached")  # pragma: no cover


class AsyncRateLimiter(BaseRateLimiter):
    """This is a Rate Limiter implementation for asynchronous functions
    (like geocoders with :class:`geopy.adapters.BaseAsyncAdapter`).

    Examples::

        from geopy.adapters import AioHTTPAdapter
        from geopy.extra.rate_limiter import AsyncRateLimiter
        from geopy.geocoders import Nominatim

        async with Nominatim(
            user_agent="specify_your_app_name_here",
            adapter_factory=AioHTTPAdapter,
        ) as geolocator:

            search = ["moscow", "paris", "berlin", "tokyo", "beijing"]
            geocode = AsyncRateLimiter(geolocator.geocode, min_delay_seconds=1)
            locations = [await geocode(s) for s in search]

            search = [
                (55.47, 37.32), (48.85, 2.35), (52.51, 13.38),
                (34.69, 139.40), (39.90, 116.39)
            ]
            reverse = AsyncRateLimiter(geolocator.reverse, min_delay_seconds=1)
            locations = [await reverse(s) for s in search]

    AsyncRateLimiter class is safe to use across multiple concurrent tasks.
    If geocoding service's responses are slower than `min_delay_seconds`,
    then you can benefit from parallelizing the work::

        import asyncio

        async with OpenMapQuest(
            api_key="...", adapter_factory=AioHTTPAdapter
        ) as geolocator:

            geocode = AsyncRateLimiter(geolocator.geocode, min_delay_seconds=1/20)
            locations = await asyncio.gather(*(geocode(s) for s in search))

    .. versionadded:: 2.0
    """

    def __init__(
        self,
        func,
        *,
        min_delay_seconds=0.0,
        max_retries=2,
        error_wait_seconds=5.0,
        swallow_exceptions=True,
        return_value_on_exception=None
    ):
        """
        :param callable func:
            A function which should be wrapped by the rate limiter.

        :param float min_delay_seconds:
            Minimum delay in seconds between the wrapped ``func`` calls.
            To convert :abbr:`RPS (Requests Per Second)` rate to
            ``min_delay_seconds`` you need to divide 1 by RPS. For example,
            if you need to keep the rate at 20 RPS, you can use
            ``min_delay_seconds=1/20``.

        :param int max_retries:
            Number of retries on exceptions. Only
            :class:`geopy.exc.GeocoderServiceError` exceptions are
            retried -- others are always re-raised. ``max_retries + 1``
            requests would be performed at max per query. Set
            ``max_retries=0`` to disable retries.

        :param float error_wait_seconds:
            Time to wait between retries after errors. Must be
            greater or equal to ``min_delay_seconds``.

        :param bool swallow_exceptions:
            Should an exception be swallowed after retries? If not,
            it will be re-raised. If yes, the ``return_value_on_exception``
            will be returned.

        :param return_value_on_exception:
            Value to return on failure when ``swallow_exceptions=True``.

        """
        super().__init__(
            min_delay_seconds=min_delay_seconds,
            max_retries=max_retries,
            swallow_exceptions=swallow_exceptions,
            return_value_on_exception=return_value_on_exception,
        )
        self.func = func
        self.error_wait_seconds = error_wait_seconds
        assert error_wait_seconds >= min_delay_seconds
        assert max_retries >= 0

    async def _sleep(self, seconds):  # pragma: no cover
        logger.debug(type(self).__name__ + " sleep(%r)", seconds)
        await asyncio.sleep(seconds)

    async def _acquire_request_slot(self):
        for wait in self._acquire_request_slot_gen():
            await self._sleep(wait)

    async def __call__(self, *args, **kwargs):
        gen = self._retries_gen(args, kwargs)
        for _ in gen:
            await self._acquire_request_slot()
            try:
                return await self.func(*args, **kwargs)
            except self._retry_exceptions as e:
                if gen.throw(e):
                    # A final try
                    return self._handle_exc(args, kwargs)
                await self._sleep(self.error_wait_seconds)

        raise RuntimeError("Should not have been reached")  # pragma: no cover
