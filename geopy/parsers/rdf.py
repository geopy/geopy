try:
    import xml.etree
except ImportError:
    import ElementTree
else:
    from xml.etree import ElementTree

from geopy import Point, Location
from geopy.parsers import Parser
from geopy.util import reversed

class GeoVocabulary(Parser):
    GEO_NS = "http://www.w3.org/2003/01/geo/wgs84_pos#"
    POINT_CLASS = 'Point'
    LATITUDE_PROPERTY = 'lat'
    LONGITUDE_PROPERTY = 'long'
    ALTITUDE_PROPERTY = 'alt'
    
    def __init__(self, ignore_invalid=True, point_class=False):
        self.ignore_invalid = ignore_invalid
        self.point_class = point_class
    
    def find(self, document):
        if isinstance(document, basestring):
            document = ElementTree.fromstring(document)
        elif not ElementTree.iselement(document):
            document = ElementTree.parse(document)
        
        point_qname = self._get_qname(self.POINT_CLASS)
        lat_qname = self._get_qname(self.LATITUDE_PROPERTY)
        long_qname = self._get_qname(self.LONGITUDE_PROPERTY)
        alt_qname = self._get_qname(self.ALTITUDE_PROPERTY)
        
        queue = [document]
        while queue:
            element = queue.pop()
            if not self.point_class or element.tag == point_qname:
                lat_el = element.find(lat_qname)
                long_el = element.find(long_qname)
                alt_el = element.find(alt_qname)
                if lat_el is not None and long_el is not None:
                    latitude = lat_el.text
                    longitude = long_el.text
                    altitude = alt_el and alt_el.text
                    try:
                        point = Point((latitude, longitude, altitude))
                    except (TypeError, ValueError):
                        if not self.ignore_invalid:
                            raise
                    else:
                        yield Location(None, point)
                
                queue.extend(reversed(element))
    
    def _get_qname(self, name):
        return "{%s}%s" % (self.GEO_NS, name)
