from geopy import Point
from geopy.util import NULL_HANDLER
from geopy.parsers.iso8601 import parse_iso8601

import sys, re, logging
from xml.etree import ElementTree

log = logging.getLogger(__name__)
log.addHandler(NULL_HANDLER)

class VersionError(Exception):
    pass

class Waypoint(Point):
    '''
    A `Waypoint` is a geopy `Point` with additional waypoint metadata as
    defined by the GPX format specification.
    '''

    @classmethod
    def from_xml_names(cls, attrs, children):
        '''
        Construct a new Waypoint from dictionaries of attribute and child
        element names corresponding to GPX waypoint information, as parsed
        by the `GPX` class.
        '''
        lat = attrs['lat']
        lon = attrs['lon']
        if 'ele' in children:
            ele = children['ele']
        else:
            ele = None
        w = cls(lat, lon, ele)
        if 'time' in children:
            w.timestamp = children['time']
        if 'name' in children:
            w.name = children['name']
        if 'desc' in children:
            w.description = children['desc']
        if 'cmt' in children:
            w.comment = children['cmt']
        if 'src' in children:
            w.source = children['src']
        if 'sym' in children:
            w.symbol = children['sym']
        if 'type' in children:
            w.classification = children['type']
        if 'fix' in children:
            w.fix = children['fix']
        if 'sat' in children:
            w.num_satellites = children['sat']
        if 'ageofdgpsdata' in children:
            w.age = children['ageofdgpsdata']
        if 'dgpsid' in children:
            w.dgpsid = children['dgpsid']
        return w

class _Attr(object):
    '''
    Value wrapper for allowing interfaces to access attribute values with
    `obj.text`
    '''
    def __init__(self, value):
        self.text = value

class GPX(object):
    GPX_NS = "http://www.topografix.com/GPX/1/1"
    FILE_EXT = '.gpx'
    MIME_TYPE = 'application/gpx+xml'
    VERSION = '1.1'
    FIX_TYPES =  set(('none', '2d', '3d', 'dgps', 'pps'))
    DECIMAL_RE = re.compile(r'([+-]?\d*\.?\d+)$')

    # Each "type tuple" is a tuple of two items:
    #   1. Dictionary of attributes in the type
    #   2. Dictionary of child elements that can appear in the type

    GPX_TYPE = ({'version': 'string', 'creator': 'string'}, {
        'metadata': 'metadata', 'wpt': ['waypoint'], 'rte': ['route'],
        'trk': ['track'], 'extensions': 'extensions'
    })
    METADATA_TYPE = ({}, {
        'name': 'string', 'desc': 'string', 'author': 'person',
        'copyright': 'copyright', 'link': ['link'], 'time': 'datetime',
        'keywords': 'string', 'bounds': 'bounds', 'extensions': 'extensions'
    })
    WAYPOINT_TYPE = ({'lat': 'decimal', 'lon': 'decimal'}, {
        'ele': 'decimal', 'time': 'datetime', 'magvar': 'degrees',
        'geoidheight': 'decimal', 'name': 'string', 'cmt': 'string',
        'desc': 'string', 'src': 'string', 'link': ['link'], 'sym': 'string',
        'type': 'string', 'fix': 'fix', 'sat': 'unsigned', 'hdop': 'decimal',
        'vdop': 'decimal', 'pdop': 'decimal', 'ageofdgpsdata': 'decimal',
        'dgpsid': 'dgpsid', 'extensions': 'extensions'
    })
    ROUTE_TYPE = ({}, {
        'name': 'string', 'cmt': 'string', 'desc': 'string', 'src': 'string',
        'link': ['link'], 'number': 'unsigned', 'type': 'string',
        'extensions': 'extensions', 'rtept': ['waypoint']
    })
    TRACK_TYPE = ({}, {
        'name': 'string', 'cmt': 'string', 'desc': 'string', 'src': 'string',
        'link': ['link'], 'number': 'unsigned', 'type': 'string',
        'extensions': 'extensions', 'trkseg': ['segment']
    })
    TRACK_SEGMENT_TYPE = ({},
        {'trkpt': ['waypoint'], 'extensions': 'extensions'}
    )
    COPYRIGHT_TYPE = (
        {'author': 'string'}, {'year': 'year', 'license': 'uri'}
    )
    LINK_TYPE = ({'href': 'uri'}, {'text': 'string', 'type': 'string'})
    EMAIL_TYPE = ({'id': 'string', 'domain': 'string'}, {})
    PERSON_TYPE = ({}, {'name': 'string', 'email': 'email', 'link': 'link'})
    POINT_TYPE = ({'lat': 'longitude', 'lon': 'longitude'},
        {'ele': 'decimal', 'time': 'datetime'}
    )
    POINT_SEGMENT_TYPE = ({}, {'pt': ['point']})
    BOUNDS_TYPE = ({
        'minlat': 'latitude', 'minlon': 'longitude',
        'maxlat': 'latitude', 'maxlon': 'longitude'
    }, {})

    def __init__(self, document=None, cache=True):
        self.cache = cache
        self._waypoints = {}
        self._routes = {}
        self._tracks = {}

        self.type_handlers = {
            'string': lambda e: e.text,
            'uri': lambda e: e.text,
            'datetime': self._parse_datetime_element,
            'decimal': self._parse_decimal,
            'dgpsid': self._parse_dgps_station,
            'email': self._parse_email,
            'link': self._parse_link,
            'year': self._parse_int,
            'waypoint': self._parse_waypoint,
            'segment': self._parse_segment,
            'unsigned': self._parse_unsigned,
            'degrees': self._parse_degrees,
            'fix': self._parse_fix,
            'extensions': self._parse_noop,
        }

        if document is not None:
            self.open(document)

    def open(self, string_or_file):
        if isinstance(string_or_file, basestring):
            string_or_file = ElementTree.fromstring(string_or_file)
        elif not ElementTree.iselement(string_or_file):
            string_or_file = ElementTree.parse(string_or_file)
        if string_or_file.getroot().tag == self._get_qname('gpx'):
            self._root = string_or_file.getroot()

    @property
    def version(self):
        if not hasattr(self, '_version'):
            version = self._root.get('version')
            if version == self.VERSION:
                self._version = version
            else:
                raise VersionError("%r" % (version,))
        return self._version

    @property
    def creator(self):
        if not hasattr(self, '_creator'):
            self._creator = self._root.get('creator')
        return self._creator

    @property
    def metadata(self):
        if not hasattr(self, '_metadata'):
            metadata_qname = self._get_qname('metadata')
            metadata = {}
            element = self._root.find(metadata_qname)
            if element is not None:
                single, multi = self.METADATA
                metadata.update(self._child_dict(element, single, multi))
                for tag in ('name', 'desc', 'time', 'keywords'):
                    if tag in metadata:
                        metadata[tag] = metadata[tag]
                if 'time' in metadata:
                    metadata['time'] = self._parse_datetime(metadata['time'])
            self._metadata = metadata
        return self._metadata

    @property
    def waypoints(self):
        tag = self._get_qname('wpt')
        return self._cache_parsed(tag, self._parse_waypoint, self._waypoints)

    def _parse_waypoint(self, element):
        waypoint = {}
        point = Point(element.get('lat'), element.get('lon'))

    def _parse_segment(self, element):
        pass

    @property
    def routes(self):
        tag = self._get_qname('rte')
        return self._cache_parsed(tag, self._parse_route, self._routes)

    def _parse_route(self, element):
        pass

    @property
    def route_names(self):
        for route in self._root.findall(self._get_qname('rte')):
            yield route.findtext(self._get_qname('name'))

    @property
    def waypoints(self):
        return self.get_waypoints()

    def get_waypoints(self, route=None):
        if route is None:
            root = self._root
            waypoint_name = self._get_qname('wpt')
        else:
            root = self.get_route_by_name(route)
            waypoint_name = self._get_qname('rtept')

        for rtept in root.findall(waypoint_name):
            attrs, children = self._parse_type(rtept, self.WAYPOINT_TYPE)
            yield Waypoint.from_xml_names(attrs, children)

    def get_route_by_name(self, route):
        if isinstance(route, basestring):
            name = route
            index = 0
        else:
            name, index = route

        seen_index = 0
        for rte in self._root.findall(self._get_qname('rte')):
            rname = rte.findtext(self._get_qname('name'))
            if rname == name:
                if not seen_index == index:
                    seen_index = seen_index + 1
                else:
                    return rte

        return None

    @property
    def tracks(self):
        tag = self._get_qname('rte')
        return self._cache_parsed(tag, self._parse_track, self._tracks)

    def _parse_track(self, element):
        pass

    def _parse_type(self, element, type_def):
        attr_types, child_types = type_def
        attrs = {}
        children = {}
        for attr, handler in attr_types.iteritems():
            value = element.get(attr)
            type_func = self.type_handlers[handler]
            attrs[attr] = type_func(_Attr(value))
        for tag, handler in child_types.iteritems():
            values = []
            all = False
            if isinstance(handler, list):
                all = True
                type_func = self.type_handlers[handler[0]]
            else:
                type_func = self.type_handlers[handler]
            for e in element.findall(self._get_qname(tag)):
                values.append(type_func(e))
            if len(values) > 0:
                if all:
                    children[tag] = values
                else:
                    children[tag] = values[-1]
        return attrs, children

    @property
    def extensions(self):
        extensions_qname = self._get_qname('extensions')

    def _cache_parsed(self, tag, parse_func, cache):
        i = -1
        for i in xrange(len(cache)):
            item = cache[i]
            if item is not None:
                yield item
        for element in self._root:
            if element.tag == tag:
                i += 1
                item = parse_func(element)
                if self.cache:
                    cache[i] = item
                if item is not None:
                    yield item

    def _parse_decimal(self, element):
        value = element.text
        match = re.match(self.DECIMAL_RE, value)
        if match:
            return float(match.group(1))
        else:
            raise ValueError("Invalid decimal value: %r" % (value,))

    def _parse_degrees(self, element):
        value = self._parse_decimal(element)
        if 0 <= value <= 360:
            return value
        else:
            raise ValueError("Value out of range [0, 360]: %r" % (value,))

    def _parse_dgps_station(self, element):
        value = int(element.text)
        if 0 <= value <= 1023:
            return value
        else:
            raise ValueError("Value out of range [0, 1023]: %r" % (value,))

    def _parse_datetime(self, value):
        return parse_iso8601(value)

    def _parse_datetime_element(self, element):
        return self._parse_datetime(element.text)

    def _parse_email(self, element):
        value = element.text
        if not value:
            name = element.get('id')
            domain = element.get('domain')
            if name and domain:
                return '@'.join((name, domain))
        return value or None

    def _parse_link(self, element):
        pass

    def _parse_int(self, element):
        return int(element.text)

    def _parse_unsigned(self, element):
        return int(element.text)

    def _parse_fix(self, element):
        value = element.text
        if value in self.FIX_TYPES:
            return value
        else:
            raise ValueError("Value is not a valid fix type: %r" % (value,))

    def _parse_string(self, element):
        return element.text

    def _parse_noop(self, element):
        return element

    def _child_dict(self, element, single, multi):
        single = dict([(self._get_qname(tag), tag) for tag in single])
        multi = dict([(self._get_qname(tag), tag) for tag in multi])
        limit = len(single)
        d = {}
        if limit or multi:
            for child in element:
                if child.tag in single:
                    name = single.pop(child.tag)
                    d[name] = child
                    limit -= 1
                elif child.tag in multi:
                    name = multi[child.tag]
                    d.setdefault(name, []).append(child)
                if not limit and not multi:
                    break
        return d

    def _get_qname(self, name):
        return "{%s}%s" % (self.GPX_NS, name)
