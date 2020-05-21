"""
Utils.
"""

import logging

from geopy.compat import py3k, text_type

if not py3k:  # pragma: no cover
    NUMBER_TYPES = (int, long, float)  # noqa
else:  # pragma: no cover
    NUMBER_TYPES = (int, float)  # long -> int in Py3k
try:
    from decimal import Decimal
    NUMBER_TYPES = NUMBER_TYPES + (Decimal, )
except ImportError:  # pragma: no cover
    pass


__version__ = "1.22.0"

logger = logging.getLogger('geopy')


def pairwise(seq):
    """
    Pair an iterable, e.g., (1, 2, 3, 4) -> ((1, 2), (2, 3), (3, 4))
    """
    for i in range(0, len(seq) - 1):
        yield (seq[i], seq[i + 1])


def join_filter(sep, seq, pred=bool):
    """
    Join with a filter.
    """
    return sep.join([text_type(i) for i in seq if pred(i)])


def decode_page(page):
    """
    Return unicode string of geocoder results.

    Nearly all services use JSON, so assume UTF8 encoding unless the
    response specifies otherwise.
    """
    if hasattr(page, 'read'):  # urllib
        if py3k:
            encoding = page.headers.get_param("charset") or "utf-8"
        else:
            encoding = page.headers.getparam("charset") or "utf-8"
        return text_type(page.read(), encoding=encoding)
    else:  # requests?
        encoding = page.headers.get("charset") or "utf-8"
        return text_type(page.content, encoding=encoding)


def get_version():
    return __version__
