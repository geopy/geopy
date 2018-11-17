import inspect
import sys
import warnings
from urllib.error import HTTPError
from urllib.parse import parse_qs, quote, quote_plus, urlencode, urlparse
from urllib.request import (
    HTTPSHandler,
    ProxyHandler,
    Request,
    URLError,
    build_opener,
    urlopen,
)


def cmp(a, b):
    return (a > b) - (a < b)


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


def _is_urllib_context_supported(HTTPSHandler_=HTTPSHandler):
    context_arg = 'context'
    argspec = inspect.getfullargspec(HTTPSHandler_.__init__)
    return context_arg in argspec.args or context_arg in argspec.kwonlyargs


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
