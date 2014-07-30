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
        """
        if hasattr(page.headers, "getparam"): # urllib
            encoding = page.headers.getparam("charset") or "iso-8859-1"
            return unicode(page.read(), encoding=encoding).encode('utf-8')
        else: # requests?
            encoding = page.headers.get("charset") or "iso-8859-1"
            return unicode(page.content, encoding=encoding).encode('utf-8')
else:
    def decode_page(page):
        """
        Return unicode string of geocoder results.
        """
        if hasattr(page.headers, "getparam"): # urllib
            encoding = page.headers.getparam("charset") or "iso-8859-1"
            return unicode(page.read(), encoding=encoding).encode('utf-8')
        else: # requests?
            encoding = page.headers.get("charset") or "iso-8859-1"
            return unicode(page.content, encoding=encoding).encode('utf-8')
