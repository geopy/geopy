import re
from BeautifulSoup import BeautifulSoup, SoupStrainer
from geopy import Point, Location
from geopy.parsers import Parser
from geopy.util import unescape

FLOAT_RE = re.compile(r'([+-]?\d*\.?\d+)$')

class ICBMMetaTag(Parser):
    META_NAME = 'ICBM'
    
    def __init__(self, ignore_invalid=True):
        self.ignore_invalid = ignore_invalid
    
    def find(self, document):
        strainer = SoupStrainer('meta', attrs={'name': self.META_NAME})
        if not isinstance(document, BeautifulSoup):
            elements = BeautifulSoup(document, parseOnlyThese=strainer)
        else:
            elements = document.findAll(strainer)
        
        for element in elements:
            lat_long = element.get('content')
            if lat_long or not self.ignore_invalid:
                try:
                    point = Point(unescape(lat_long))
                except (TypeError, ValueError):
                    if not self.ignore_invalid:
                        raise
                else:
                    yield Location(None, point)


class GeoMetaTag(Parser):
    META_NAME = re.compile(r'geo\.(\w+)')
    
    def __init__(self, ignore_invalid=True):
        self.ignore_invalid = ignore_invalid
    
    def find(self, document):
        strainer = SoupStrainer('meta', attrs={'name': self.META_NAME})
        if not isinstance(document, BeautifulSoup):
            elements = BeautifulSoup(document, parseOnlyThese=strainer)
        else:
            elements = document.findAll(strainer)
        
        attrs = {}
        for element in elements:
            meta_name = element['name']
            attr_name = re.match(self.META_NAME, meta_name).group(1)
            value = element.get('content')
            if attr_name in attrs:
                location = self._get_location(attrs)
                if location is not None:
                    yield location
                attrs.clear()
            attrs[attr_name] = value and unescape(value)
        
        location = self._get_location(attrs)
        if location is not None:
            yield location
    
    def _get_location(self, attrs):
        position = attrs.pop('position')
        name = attrs.pop('placename')
        if position is not None:
            if position or not self.ignore_invalid:
                try:
                    point = Point(position)
                except (TypeError, ValueError):
                    if not self.ignore_invalid:
                        raise
                else:
                    return Location(name, point, attrs)


class GeoMicroformat(Parser):
    GEO_CLASS = re.compile(r'\s*geo\s*')
    LATITUDE_CLASS = re.compile(r'\s*latitude\s*')
    LONGITUDE_CLASS = re.compile(r'\s*longitude\s*')
    VALUE_CLASS = re.compile(r'\s*value\s*')
    SEP = re.compile(r'\s*;\s*')
    
    def __init__(self, ignore_invalid=True, shorthand=True, abbr_title=True, value_excerpting=True):
        self.ignore_invalid = ignore_invalid
        self.shorthand = shorthand
        self.abbr_title = abbr_title
        self.value_excerpting = value_excerpting
    
    def find(self, document):
        strainer = SoupStrainer(attrs={'class': self.GEO_CLASS})
        if not isinstance(document, BeautifulSoup):
            elements = BeautifulSoup(document, parseOnlyThese=strainer)
        else:
            elements = document.findAll(strainer)
        
        for element in elements:
            preformatted = element.name == 'pre'
            lat_element = element.find(attrs={'class': self.LATITUDE_CLASS})
            long_element = element.find(attrs={'class': self.LONGITUDE_CLASS})
            latitude = None
            longitude = None
            if lat_element and long_element:
                latitude = self._get_value(lat_element, preformatted)
                longitude = self._get_value(long_element, preformatted)
            elif self.shorthand:
                lat_long = re.split(self.SEP, self._get_value(element), 1)
                if len(lat_long) == 2:
                    latitude, longitude = lat_long
            if latitude and longitude:
                lat_match = FLOAT_RE.match(unescape(latitude))
                long_match = FLOAT_RE.match(unescape(longitude))
                if lat_match and long_match:
                    latitude = float(lat_match.group(1))
                    longitude = float(long_match.group(1))
                    text = unescape(self._get_text(element).strip())
                    name = re.sub('\s+', ' ', text)
                    yield Location(name, (latitude, longitude))
    
    def _get_text(self, element, preformatted=False):
        if isinstance(element, basestring):
            if not preformatted:
                return re.sub('\s+', ' ', element)
            else:
                return element
        elif element.name == 'br':
            return '\n'
        else:
            pre = preformatted or element.name == 'pre'
            return "".join([self._get_text(node, pre) for node in element])
    
    def _get_value(self, element, preformatted=False):
        if self.value_excerpting:
            value_nodes = element.findAll(attrs={'class': self.VALUE_CLASS})
            if value_nodes:
                pre = preformatted or element.name == 'pre'
                values = [self._get_text(node, pre) for node in value_nodes]
                return "".join(values)
        if self.abbr_title and element.name == 'abbr':
            value = element.get('title')
            if value is not None:
                return value
        return self._get_text(element, preformatted)
