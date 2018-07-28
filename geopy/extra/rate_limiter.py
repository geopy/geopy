# coding: utf-8
from timeit import default_timer
from itertools import count, chain

from geopy.util import logger
from geopy.exc import GeocoderServiceError
from geopy.compat import sleep_at_least


def _is_last_gen(count):
    """list(_is_last_gen(2)) -> [False, False, True]"""
    return chain((False for _ in range(count)), [True])


class RateLimiter(object):
    """RateLimiter allows to perform bulk operations while gracefully
    handling error responses and adding delays when needed.

    .. note::
       This is an experimental API which might be changed in the future.
       Please report any bugs, issues and suggestions on the issue tracker.

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

    Before using this class, please consult with the Geocoding service
    ToS, which might explicitly consider bulk requests (even throttled)
    a violation.

    .. versionadded:: 1.16.0
    """

    def __init__(self, func, min_delay_seconds=0.0, max_retries=2,
                 error_wait_seconds=5.0,
                 swallow_exceptions=True, return_value_on_exception=None):
        """
        :param callable func:
            A function which should be wrapped by the :class:`.RateLimiter`.

        :param float min_delay_seconds:
            Minimum delay in seconds between the wrapped ``func`` calls.

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
        self.func = func
        self.min_delay_seconds = min_delay_seconds
        self.max_retries = max_retries
        self.error_wait_seconds = error_wait_seconds
        self.swallow_exceptions = swallow_exceptions
        self.return_value_on_exception = return_value_on_exception
        assert error_wait_seconds >= min_delay_seconds
        assert max_retries >= 0

        self._last_call = self._clock() - min_delay_seconds

    def _clock(self):  # pragma: no coverage
        return default_timer()

    def _sleep(self, seconds):  # pragma: no coverage
        logger.debug('RateLimiter sleep(%r)', seconds)
        sleep_at_least(seconds)

    def _sleep_between(self):
        seconds_since_last_call = self._clock() - self._last_call
        wait = self.min_delay_seconds - seconds_since_last_call
        if wait > 0:
            self._sleep(wait)

    def __call__(self, *args, **kwargs):
        self._sleep_between()

        for i, is_last_try in zip(count(), _is_last_gen(self.max_retries)):
            try:
                return self.func(*args, **kwargs)
            except GeocoderServiceError:
                if not is_last_try:
                    logger.warning(
                        'RateLimiter caught an error, retrying '
                        '(%s/%s tries). Called with (*%r, **%r).',
                        i, self.max_retries, args, kwargs, exc_info=True
                    )
                    self._sleep(self.error_wait_seconds)
                    continue

                if self.swallow_exceptions:
                    logger.warning(
                        'RateLimiter swallowed an error after %r retries. '
                        'Called with (*%r, **%r).',
                        i, args, kwargs, exc_info=True
                    )
                    return self.return_value_on_exception
                else:
                    raise
            finally:
                self._last_call = self._clock()
