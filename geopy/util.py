"""
Utils.
"""

import re
import logging
try: # Py2k
    import htmlentitydefs # pylint: disable=F0401
except ImportError: # Py3k
    import html.entities as htmlentitydefs # pylint: disable=F0401
import xml.dom.minidom
from xml.parsers.expat import ExpatError

try:
    NUMBER_TYPES = (int, long, float)
except NameError:
    NUMBER_TYPES = (int, float) # float -> int in Py3k
try:
    from decimal import Decimal
    NUMBER_TYPES = NUMBER_TYPES + (Decimal, )
except ImportError:
    pass

from geopy.compat import py3k, string_compare

class NullHandler(logging.Handler):
    """
    No output.
    """

    def emit(self, record):
        pass

logger = logging.getLogger('geopy') # pylint: disable=C0103
logger.addHandler(NullHandler())


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

if not py3k:
    def join_filter(sep, seq, pred=bool):
        """
        TODO docs.
        """
        return sep.join([unicode(i) for i in seq if pred(i)])
else:
    def join_filter(sep, seq, pred=bool):
        """
        TODO docs.
        """
        return sep.join([str(i) for i in seq if pred(i)])


def get_encoding(page, contents=None):
    """
    TODO docs.
    """
    # TODO: clean up Py3k support
    if not py3k:
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
    if not py3k:
        return unicode(contents, encoding=encoding).encode('utf-8')
    else:
        return str(contents, encoding=encoding)

def get_first_text(node, tag_names, strip=None):
    """
    TODO docs.
    """
    if isinstance(tag_names, string_compare):
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
