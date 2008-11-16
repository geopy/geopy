import xml.dom.minidom
from BeautifulSoup import BeautifulSoup
from geopy.geocoders.base import Geocoder
from geopy.point import Point
from geopy.location import Location
from geopy import util

try:
    set
except NameError:
    from sets import Set as set

class SemanticMediaWiki(Geocoder):
    def __init__(self, format_url, attributes=None, relations=None,
                 prefer_semantic=False, transform_string=None):
        self.format_url = format_url
        self.attributes = attributes
        self.relations = relations
        self.prefer_semantic = prefer_semantic
        self.transform_string = transform_string
    
    def get_url(self, string):
        return self.format_url % self.transform_string(string)

    def parse_rdf_link(self, page, mime_type='application/rdf+xml'):
        """Parse the URL of the RDF link from the <head> of ``page``."""
        soup = BeautifulSoup(page)
        link = soup.head.find('link', rel='alternate', type=mime_type)
        return link and link['href'] or None
    
    def parse_rdf_things(self, data):
        dom = xml.dom.minidom.parseString(data)
        thing_map = {}
        things = dom.getElementsByTagName('smw:Thing')
        things.reverse()
        for thing in things:
            name = thing.attributes['rdf:about'].value
            articles = thing.getElementsByTagName('smw:hasArticle')
            things[name] = articles[0].attributes['rdf:resource'].value
        
        return (things, thing)
    
    def transform_semantic(self, string):
        """Normalize semantic attribute and relation names by replacing spaces
        with underscores and capitalizing the result."""
        return string.replace(' ', '_').capitalize()

    def get_relations(self, thing, relations=None):
        if relations is None:
            relations = self.relations
        
        for relation in relations:
            relation = self.transform_semantic(relation)
            for node in thing.getElementsByTagName('relation:' + relation):
                resource = node.attributes['rdf:resource'].value
                yield (relation, resource)
    
    def get_attributes(self, thing, attributes=None):
        if attributes is None:
            attributes = self.attributes

        for attribute in attributes:
            attribute = self.transform_semantic(attribute)
            for node in thing.getElementsByTagName('attribute:' + attribute):
                value = node.firstChild.nodeValue.strip()
                yield (attribute, value)
    
    def get_thing_label(self, thing):
        return util.get_first_text(thing, 'rdfs:label')
    
    def geocode_url(self, url, attempted=None):
        if attempted is None:
            attempted = set()

        print "Fetching %s..." % url
        page = urlopen(url)
        soup = BeautifulSoup(page)

        rdf_url = self.parse_rdf_link(soup)
        print "Fetching %s..." % rdf_url
        page = urlopen(rdf_url)

        things, thing = self.parse_rdf(page)
        name = self.get_label(thing)

        attributes = self.get_attributes(thing)
        for attribute, value in attributes:
            latitude, longitude = util.parse_geo(value)
            if None not in (latitude, longitude):
                break

        if None in (latitude, longitude):
            relations = self.get_relations(thing)
            for relation, resource in relations:
                url = things.get(resource, resource)
                if url in tried: # Avoid cyclic relationships.
                    continue
                tried.add(url)
                name, (latitude, longitude) = self.geocode_url(url, tried)
                if None not in (name, latitude, longitude):
                    break

        return (name, (latitude, longitude))