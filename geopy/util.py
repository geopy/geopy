"""
Utils.
"""

import logging
from geopy.compat import py3k

if not py3k: # pragma: no cover
    NUMBER_TYPES = (int, long, float)
else: # pragma: no cover
    NUMBER_TYPES = (int, float) # long -> int in Py3k
try:
    from decimal import Decimal
    NUMBER_TYPES = NUMBER_TYPES + (Decimal, )
except ImportError: # pragma: no cover
    pass


__version__ = "1.11.0"


class NullHandler(logging.Handler):
    """
    No output.
    """

    def emit(self, record):
        pass

logger = logging.getLogger('geopy') # pylint: disable=C0103
logger.setLevel(logging.CRITICAL)


def pairwise(seq):
    """
    Pair an iterable, e.g., (1, 2, 3, 4) -> ((1, 2), (3, 4))
    """
    for i in range(0, len(seq) - 1):
        yield (seq[i], seq[i + 1])


if not py3k:
    def join_filter(sep, seq, pred=bool):
        """
        Join with a filter.
        """
        return sep.join([unicode(i) for i in seq if pred(i)])
else:
    def join_filter(sep, seq, pred=bool):
        """
        Join with a filter.
        """
        return sep.join([str(i) for i in seq if pred(i)])


if not py3k:
    def decode_page(page):
        """
        Return unicode string of geocoder results.

        Nearly all services use JSON, so assume UTF8 encoding unless the
        response specifies otherwise.
        """
        if hasattr(page, 'read'): # urllib
            # note getparam in py2
            encoding = page.headers.getparam("charset") or "utf-8"
            return unicode(page.read(), encoding=encoding)
        else: # requests?
            encoding = page.headers.get("charset", "utf-8")
            return unicode(page.content, encoding=encoding)
else:
    def decode_page(page):
        """
        Return unicode string of geocoder results.

        Nearly all services use JSON, so assume UTF8 encoding unless the
        response specifies otherwise.
        """
        if hasattr(page, 'read'): # urllib
            # note get_param in py3
            encoding = page.headers.get_param("charset") or "utf-8"
            return str(page.read(), encoding=encoding)
        else: # requests?
            encoding = page.headers.get("charset") or "utf-8"
            return str(page.content, encoding=encoding)


def get_version():
    from geopy.version import GEOPY_VERSION
    return str(GEOPY_VERSION)


