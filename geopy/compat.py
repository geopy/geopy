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
        build_opener, ProxyHandler, URLError)
    from urllib.error import HTTPError # pylint: disable=W0611,F0401,W0611,E0611
else: # pragma: no cover
    from urllib import urlencode, quote # pylint: disable=W0611,F0401,W0611,E0611
    from urllib2 import (Request, HTTPError,   # pylint: disable=W0611,F0401,W0611,E0611
        ProxyHandler, URLError, urlopen, build_opener)
