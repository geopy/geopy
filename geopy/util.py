"""
Utils.
"""

import logging
from collections import namedtuple
from geopy.compat import py3k, text_type, isfinite

if not py3k: # pragma: no cover
    NUMBER_TYPES = (int, long, float)
else: # pragma: no cover
    NUMBER_TYPES = (int, float) # long -> int in Py3k
try:
    from decimal import Decimal
    NUMBER_TYPES = NUMBER_TYPES + (Decimal, )
except ImportError: # pragma: no cover
    pass


__version__ = "1.12.0"

logger = logging.getLogger('geopy') # pylint: disable=C0103


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
    if hasattr(page, 'read'): # urllib
        if py3k:
            encoding = page.headers.get_param("charset") or "utf-8"
        else:
            encoding = page.headers.getparam("charset") or "utf-8"
        return text_type(page.read(), encoding=encoding)
    else: # requests?
        encoding = page.headers.get("charset") or "utf-8"
        return text_type(page.content, encoding=encoding)


def get_version():
    return __version__


def invert_bool(bool_or_none):
    """
    Basically this is a boolean negation, but None is returned as-is instead
    of being converted to True.
    """
    if bool_or_none is None:
        return None
    return not bool_or_none


class ValidatedNumber(namedtuple('ValidatedNumber',
                                 ('is_invalid_type', 'is_infinite',
                                  'is_outside_boundaries'))):
    """
    Perform validation of a number and tell what's wrong with it by
    setting corresponding boolean flags to False. This is internal API.
    """
    __slots__ = ()  # namedtuple doesn't have __dict__, don't use it there too

    @classmethod
    def all_valid(cls):
        """
        Construct a valid ValidatedNumber.
        """
        return _validated_number_all_valid

    @classmethod
    def from_number(cls, x, boundaries=None):
        """
        Construct a ValidatedNumber from a number.
        """
        is_number_type = isinstance(x, NUMBER_TYPES)
        is_finite = isfinite(x) if is_number_type else None
        is_within_boundaries = (boundaries[0] <= x <= boundaries[1]
                                if is_number_type and is_finite and
                                boundaries else None)
        return cls(not is_number_type, invert_bool(is_finite),
                   invert_bool(is_within_boundaries))

    def __bool__(self):
        """
        Is this ValidatedNumber represents a valid number?
        """
        return (not self.is_invalid_type and not self.is_infinite and
                not self.is_outside_boundaries)

    __nonzero__ = __bool__  # py2

    def __or__(self, other):
        """
        Return a new ValidatedNumber which combines errors from the two
        ValidatedNumber instances.
        """
        cls = ValidatedNumber
        if not isinstance(other, cls):
            return NotImplemented
        if self == other:  # perf optimization
            return self
        return cls(self.is_invalid_type or other.is_invalid_type,
                   self.is_infinite or other.is_infinite,
                   self.is_outside_boundaries or other.is_outside_boundaries)


# Create an empty ValidatedNumber once for performance considerations.
_validated_number_all_valid = ValidatedNumber(None, None, None)
