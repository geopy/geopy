"""
Compatibility...
"""

import sys

py3k = sys.version_info >= (3, 0)

if py3k:
    string_compare = str
else:
    string_compare = (str, unicode)

try:
    from urllib2 import HTTPError # pylint: disable=W0611,F0401,W0611,E0611
except ImportError:
    from urllib.error import HTTPError # pylint: disable=W0611,F0401,W0611,E0611

try:
    from urllib import urlencode # pylint: disable=W0611,F0401,W0611,E0611
except ImportError:
    from urllib.parse import urlencode # pylint: disable=W0611,F0401,W0611,E0611

try:
    import json
except ImportError: # pragma: no cover
    try:
        import simplejson as json # pylint: disable=F0401
    except ImportError:
        from django.utils import simplejson as json # pylint: disable=F0401

assert json is not None

try:
    from beautifulsoup4 import BeautifulSoup # pylint: disable=W0611,F0401
except ImportError:
    try:
        from BeautifulSoup import BeautifulSoup # pylint: disable=W0611,F0401
    except ImportError: # pragma: no cover
        class BeautifulSoup(object): # pylint: disable=R0903
            """
            Raise import error.
            """

            def __init__(self):
                raise ImportError(
                    "BeautifulSoup was not found. Please install BeautifulSoup "
                    "in order to use the SemanticMediaWiki Geocoder."
                ) # pylint: disable=C0103
