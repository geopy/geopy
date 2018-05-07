"""
Compatibility...
"""

import inspect
import sys
import warnings

py3k = sys.version_info >= (3, 0)

if py3k: # pragma: no cover
    string_compare = str
else: # pragma: no cover
    string_compare = (str, unicode)

if py3k:  # pragma: no cover
    text_type = str
else:  # pragma: no cover
    text_type = unicode

# Unicode compatibility, borrowed from 'six'
if py3k: # pragma: no cover
    def u(s):
        """
        Convert to Unicode with py3k
        """
        return s
else: # pragma: no cover
    def u(s):
        """
        Convert to Unicode with unicode escaping
        """
        return unicode(s.replace(r'\\', r'\\\\'), 'unicode_escape')

if py3k:
    def cmp(a, b):
        return (a > b) - (a < b)
else:
    cmp = cmp  # builtin in py2


if py3k:
    from math import isfinite
else:
    from math import isinf, isnan

    def isfinite(x):
        return not isinf(x) and not isnan(x)


if py3k: # pragma: no cover
    from urllib.parse import (urlencode, quote, # pylint: disable=W0611,F0401,W0611,E0611
                              urlparse, parse_qs)
    from urllib.request import (Request, urlopen, # pylint: disable=W0611,F0401,W0611,E0611
                                build_opener, ProxyHandler, HTTPSHandler,
                                URLError,
                                HTTPPasswordMgrWithDefaultRealm,
                                HTTPBasicAuthHandler)
    from urllib.error import HTTPError # pylint: disable=W0611,F0401,W0611,E0611

    def itervalues(d):
        """
        Function for iterating on values due to methods
        renaming between Python 2 and 3 versions
        For Python2
        """
        return iter(d.values())
    def iteritems(d):
        """
        Function for iterating on items due to methods
        renaming between Python 2 and 3 versions
        For Python2
        """
        return iter(d.items())

else: # pragma: no cover
    from urllib import urlencode as original_urlencode, quote # pylint: disable=W0611,F0401,W0611,E0611
    from urllib2 import (Request, HTTPError,   # pylint: disable=W0611,F0401,W0611,E0611
                         ProxyHandler, HTTPSHandler, URLError, urlopen,
                         build_opener,
                         HTTPPasswordMgrWithDefaultRealm,
                         HTTPBasicAuthHandler)
    from urlparse import urlparse, parse_qs

    def force_str(str_or_unicode):
        """
        Python2-only, ensures that a string is encoding to a str.
        """
        if isinstance(str_or_unicode, unicode):
            return str_or_unicode.encode('utf-8')
        else:
            return str_or_unicode

    def urlencode(query, doseq=0):
        """
        A version of Python's urllib.urlencode() function that can operate on
        unicode strings. The parameters are first cast to UTF-8 encoded strings
        and then encoded as per normal.

        Based on the urlencode from django.utils.http
        """
        if hasattr(query, 'items'):
            query = query.items()
        return original_urlencode(
            [(force_str(k),
              [force_str(i) for i in v]
              if isinstance(v, (list, tuple)) else force_str(v))
             for k, v in query],
            doseq)

    def itervalues(d):
        """
        Function for iterating on values due to methods
        renaming between Python 2 and 3 versions
        For Python3
        """
        return d.itervalues()
    def iteritems(d):
        """
        Function for iterating on items due to methods
        renaming between Python 2 and 3 versions
        For Python3
        """
        return d.iteritems()


def _is_urllib_context_supported(HTTPSHandler_=HTTPSHandler):
    context_arg = 'context'
    if py3k:
        argspec = inspect.getfullargspec(HTTPSHandler_.__init__)
        return context_arg in argspec.args or context_arg in argspec.kwonlyargs
    else:
        return context_arg in inspect.getargspec(HTTPSHandler_.__init__).args


_URLLIB_SUPPORTS_SSL_CONTEXT = _is_urllib_context_supported()


def build_opener_with_context(context=None, *handlers):
    # `context` has been added in Python 2.7.9 and 3.4.3.
    if _URLLIB_SUPPORTS_SSL_CONTEXT:
        https_handler = HTTPSHandler(context=context)
    else:
        warnings.warn(
            ("SSL context is not supported in your environment for urllib "
             "calls. Perhaps your Python version is obsolete? "
             "This probably means that TLS verification doesn't happen, "
             "which is insecure. Please consider upgrading your Python "
             "interpreter version."),
            UserWarning)
        https_handler = HTTPSHandler()
    return build_opener(https_handler, *handlers)
