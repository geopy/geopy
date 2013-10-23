"""
Utils.
"""

from sys import version_info
import re
import logging
import htmlentitydefs
import xml.dom.minidom
from xml.parsers.expat import ExpatError

try:
    from decimal import Decimal
except ImportError:
    NUMBER_TYPES = (int, long, float)
else:
    NUMBER_TYPES = (int, long, float, Decimal)

class NullHandler(logging.Handler):
    """
    No output.
    """

    def emit(self, record):
        pass

logger = logging.getLogger('geopy') # pylint: disable=C0103
logger.addHandler(NullHandler())

try:
    import json
except ImportError:
    try:
        import simplejson as json # pylint: disable=F0401
    except ImportError:
        from django.utils import simplejson as json # pylint: disable=F0401

assert json is not None

def parse_geo(val): # pylint: disable=W0613
    """
    Undefined func called in MediaWiki and SemanticMediaWiki geocoders.
    """
    raise NotImplementedError()

def pairwise(seq):
    """
    TODO docs.
    """
    for i in range(0, len(seq) - 1):
        yield (seq[i], seq[i + 1])

def join_filter(sep, seq, pred=bool):
    """
    TODO docs.
    """
    return sep.join([unicode(i) for i in seq if pred(i)])

def get_encoding(page, contents=None):
    """
    TODO docs.
    """
    # TODO: clean up Py3k support
    if version_info < (3, 0):
        charset = page.headers.getparam("charset") or None
    else:
        charset = page.headers.get_param("charset") or None
    if charset:
        return charset

    if contents:
        try:
            return xml.dom.minidom.parseString(contents).encoding
        except ExpatError:
            pass

def decode_page(page):
    """
    TODO docs.
    """
    contents = page.read()
    # HTTP 1.1 defines iso-8859-1 as the 'implied' encoding if none is given
    encoding = get_encoding(page, contents) or 'iso-8859-1'
    # TODO: clean up Py3k support
    if version_info < (3, 0):
        return unicode(contents, encoding=encoding).encode('utf-8')
    else:
        return str(contents, encoding=encoding)

def get_first_text(node, tag_names, strip=None):
    """
    TODO docs.
    """
    if isinstance(tag_names, basestring):
        tag_names = [tag_names]
    if node:
        while tag_names:
            nodes = node.getElementsByTagName(tag_names.pop(0))
            if nodes:
                child = nodes[0].firstChild
                return child and child.nodeValue.strip(strip)

def unescape(text):
    """
    Removes HTML or XML character references and entities from a text string.
    """

    def fixup(val):
        """
        Callable for re.sub below.
        """
        text = val.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is

    return re.sub(r"&#?\w+;", fixup, text)

try:
    reversed
except NameError:
    def reversed(seq): # pylint: disable=W0622
        """
        Compat for builtin... not sure which Py version this allows. todo.
        """
        i = len(seq)
        while i > 0:
            i -= 1
            yield seq[i]
else:
    reversed = reversed
