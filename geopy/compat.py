"""
Compatibility...
"""

import sys

py3k = sys.version_info >= (3, 0)

if py3k: # pragma: no cover
    string_compare = str
else: # pragma: no cover
    string_compare = (str, unicode)

try:
    from urllib2 import HTTPError # pylint: disable=W0611,F0401,W0611,E0611
except ImportError: # pragma: no cover
    from urllib.error import HTTPError # pylint: disable=W0611,F0401,W0611,E0611

try:
    from urllib import urlencode # pylint: disable=W0611,F0401,W0611,E0611
except ImportError: # pragma: no cover
    from urllib.parse import urlencode # pylint: disable=W0611,F0401,W0611,E0611
