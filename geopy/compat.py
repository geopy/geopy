"""
Compatibility...
"""

try:
    import json
except ImportError:
    try:
        import simplejson as json # pylint: disable=F0401
    except ImportError:
        from django.utils import simplejson as json # pylint: disable=F0401

assert json is not None

try:
    from BeautifulSoup import BeautifulSoup # pylint: disable=W0611,F0401
except ImportError:
    BeautifulSoup = None # pylint: disable=C0103
