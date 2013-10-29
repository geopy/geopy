"""
Utils.
"""

import logging
import xml.dom.minidom
from xml.parsers.expat import ExpatError

try:
    NUMBER_TYPES = (int, long, float)
except NameError: # pragma: no cover
    NUMBER_TYPES = (int, float) # float -> int in Py3k
try:
    from decimal import Decimal
    NUMBER_TYPES = NUMBER_TYPES + (Decimal, )
except ImportError: # pragma: no cover
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

def parse_geo(val): # pragma: no cover # pylint: disable=W0613
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

if not py3k: # pragma: no cover
    def join_filter(sep, seq, pred=bool):
        """
        TODO docs.
        """
        return sep.join([unicode(i) for i in seq if pred(i)])
else: # pragma: no cover
    def join_filter(sep, seq, pred=bool):
        """
        TODO docs.
        """
        return sep.join([str(i) for i in seq if pred(i)])


def get_encoding(page, contents=None):
    """
    TODO docs.
    """
    # TODO: clean up Py3k support.. BeautifulSoup
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
    return None

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
