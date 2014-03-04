"""
Compatibility...
"""

import sys

py3k = sys.version_info >= (3, 0)

if py3k: # pragma: no cover
    string_compare = str
else: # pragma: no cover
    string_compare = (str, unicode)

if py3k: # pragma: no cover
    from urllib.parse import urlencode, quote # pylint: disable=W0611,F0401,W0611,E0611
    from urllib.request import (Request, urlopen, # pylint: disable=W0611,F0401,W0611,E0611
        build_opener, ProxyHandler, URLError, install_opener)
    from urllib.error import HTTPError # pylint: disable=W0611,F0401,W0611,E0611
else: # pragma: no cover
    from urllib import urlencode as original_urlencode, quote # pylint: disable=W0611,F0401,W0611,E0611
    from urllib2 import (Request, HTTPError,   # pylint: disable=W0611,F0401,W0611,E0611
        ProxyHandler, URLError, urlopen, build_opener, install_opener)

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
