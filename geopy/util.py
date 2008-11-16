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
    def emit(self, record):
        pass

NULL_HANDLER = NullHandler()

def pairwise(seq):
    for i in range(0, len(seq) - 1):
        yield (seq[i], seq[i + 1])

def join_filter(sep, seq, pred=bool):
    return sep.join([unicode(i) for i in seq if pred(i)])
 
def get_encoding(page, contents=None):
    plist = page.headers.getplist()
    if plist:
        key, value = plist[-1].split('=')
        if key.lower() == 'charset':
            return value

    if contents:
        try:
            return xml.dom.minidom.parseString(contents).encoding
        except ExpatError:
            pass

def decode_page(page):
    contents = page.read()
    encoding = get_encoding(page, contents) or sys.getdefaultencoding()
    return unicode(contents, encoding=encoding).encode('utf-8')

def get_first_text(node, tag_names, strip=None):
    if isinstance(tag_names, basestring):
            tag_names = [tag_names]
    if node:
        while tag_names:
            nodes = node.getElementsByTagName(tag_names.pop(0))
            if nodes:
                child = nodes[0].firstChild
                return child and child.nodeValue.strip(strip)

def join_filter(sep, seq, pred=bool):
    return sep.join([unicode(i) for i in seq if pred(i)])

    import re, htmlentitydefs

def unescape(text):
    """
    Removes HTML or XML character references and entities from a text string.
    
    """
    def fixup(m):
        text = m.group(0)
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
    return re.sub("&#?\w+;", fixup, text)

try:
    reversed
except NameError:
    def reversed(seq):
        i = len(seq)
        while i > 0:
            i -= 1
            yield seq[i]
else:
    reversed = reversed
