import logging
from decimal import Decimal

NUMBER_TYPES = (int, float, Decimal)

__version__ = "2.0.0a0"
__version_info__ = (2, 0, 0, "a", 0)

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
    return sep.join([str(i) for i in seq if pred(i)])


def decode_page(page):
    """
    Return unicode string of geocoder results.

    Nearly all services use JSON, so assume UTF8 encoding unless the
    response specifies otherwise.
    """
    if hasattr(page, 'read'):  # urllib
        encoding = page.headers.get_param("charset") or "utf-8"
        return str(page.read(), encoding=encoding)
    else:  # requests?
        encoding = page.headers.get("charset") or "utf-8"
        return str(page.content, encoding=encoding)


def get_version():
    return __version__
