"""
:class:`.SemanticMediaWiki` geocoder.
"""

import xml.dom.minidom

from geopy.compat import BeautifulSoup

from geopy.geocoders.base import Geocoder
from geopy import util

try:
    set
except NameError:
    from sets import Set as set # pylint: disable=W0622


class SemanticMediaWiki(Geocoder):
    """
     SemanticMediaWiki geocoder. No idea on documentation. Not compliant with
     geocoder API of #geocode &c. TODO.
    """

    def __init__(self, format_url, attributes=None, relations=None, # pylint: disable=R0913
                 prefer_semantic=False, transform_string=None, proxies=None):
        super(SemanticMediaWiki, self).__init__(proxies=proxies)
        self.format_url = format_url
        self.attributes = attributes
        self.relations = relations
        self.prefer_semantic = prefer_semantic
        if transform_string:
            self._transform_string = transform_string

    def _get_url(self, string):
        """
        Generate full query URL.
        """
        return self.format_url % self._transform_string(string)

    def get_label(self, thing):
        raise NotImplementedError()

    @staticmethod
    def parse_rdf_link(page, mime_type='application/rdf+xml'):
        """Parse the URL of the RDF link from the <head> of ``page``."""
        soup = BeautifulSoup(page)
        link = soup.head.find( # pylint: disable=E1101,E1103
            'link', rel='alternate', type=mime_type
        )
        return link and link['href'] or None

    def parse_rdf(self, data):
        # TODO cleanup
        dom = xml.dom.minidom.parseString(data)
        things = dom.getElementsByTagName('smw:Thing')
        things.reverse()
        for thing in things:
            name = thing.attributes['rdf:about'].value
            articles = thing.getElementsByTagName('smw:hasArticle')
            things[name] = articles[0].attributes['rdf:resource'].value

        return (things, thing)

    @staticmethod
    def _transform_string(string): # pylint: disable=E0202
        """Normalize semantic attribute and relation names by replacing spaces
        with underscores and capitalizing the result."""
        return string.replace(' ', '_').capitalize()

    def get_relations(self, thing, relations=None):
        if relations is None:
            relations = self.relations

        for relation in relations:
            relation = self._transform_string(relation)
            for node in thing.getElementsByTagName('relation:' + relation):
                resource = node.attributes['rdf:resource'].value
                yield (relation, resource)

    def get_attributes(self, thing, attributes=None):
        if attributes is None:
            attributes = self.attributes

        for attribute in attributes:
            attribute = self._transform_string(attribute)
            for node in thing.getElementsByTagName('attribute:' + attribute):
                value = node.firstChild.nodeValue.strip()
                yield (attribute, value)

    def get_thing_label(self, thing):
        return util.get_first_text(thing, 'rdfs:label')

    def geocode_url(self, url, attempted=None):
        if attempted is None:
            attempted = set()

        util.logger.debug("Fetching %s...", url)
        page = self._call_geocoder(url)
        soup = BeautifulSoup(page)

        rdf_url = self.parse_rdf_link(soup)
        util.logger.debug("Fetching %s..." % rdf_url)
        page = self.urlopen(rdf_url)

        things, thing = self.parse_rdf(page) # TODO
        name = self.get_label(thing)

        attributes = self.get_attributes(thing)
        for _, value in attributes:
            latitude, longitude = util.parse_geo(value)
            if None not in (latitude, longitude):
                break

        if None in (latitude, longitude):
            tried = set() # TODO undefined tried -- is this right?
            relations = self.get_relations(thing)
            for _, resource in relations:
                url = things.get(resource, resource) # pylint: disable=E1103
                if url in tried: # Avoid cyclic relationships.
                    continue
                tried.add(url)
                name, (latitude, longitude) = self.geocode_url(url, tried)
                if None not in (name, latitude, longitude):
                    break

        return (name, (latitude, longitude))
