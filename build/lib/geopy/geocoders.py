import re
import csv
import sys
import getpass
import xmlrpclib
import htmlentitydefs
import xml.dom.minidom
from itertools import groupby
from urllib import quote_plus, urlencode
from urllib2 import urlopen, HTTPError
from xml.parsers.expat import ExpatError

try:
    set
except NameError:
    import sets.Set as set

# Other submodules from geopy:

import util

# Now try some more exotic modules...

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    print "BeautifulSoup was not found. " \
          "Geocoders assuming malformed markup will not work."

try:
    import simplejson
except ImportError:
    try:
        from django.utils import simplejson
    except ImportError:
        print "simplejson was not found. " \
              "Geocoders relying on JSON parsing will not work."


class Geocoder(object):
    """Base class for all geocoders."""

    def geocode(self, string):
        raise NotImplementedError


class WebGeocoder(Geocoder):
    """A Geocoder subclass with utility methods helpful for handling results
    given by web-based geocoders."""
    
    @classmethod
    def _get_encoding(cls, page, contents=None):
        """Get the last encoding (charset) listed in the header of ``page``."""
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

    @classmethod
    def _decode_page(cls, page):
        """Read the encoding (charset) of ``page`` and try to encode it using
        UTF-8."""
        contents = page.read()
        encoding = cls._get_encoding(page, contents) or sys.getdefaultencoding()
        return unicode(contents, encoding=encoding).encode('utf-8')

    @classmethod
    def _get_first_text(cls, node, tag_names, strip=None):
        """Get the text value of the first child of ``node`` with tag
        ``tag_name``. The text is stripped using the value of ``strip``."""
        if isinstance(tag_names, basestring):
            tag_names = [tag_names]
        if node:
            while tag_names:
                nodes = node.getElementsByTagName(tag_names.pop(0))
                if nodes:
                    child = nodes[0].firstChild
                    return child and child.nodeValue.strip(strip)

    @classmethod
    def _join_filter(cls, sep, seq, pred=bool):
        """Join items in ``seq`` with string ``sep`` if pred(item) is True.
        Sequence items are passed to unicode() before joining."""
        return sep.join([unicode(i) for i in seq if pred(i)])


class MediaWiki(WebGeocoder):
    def __init__(self, format_url, transform_string=None):
        """Initialize a geocoder that can parse MediaWiki pages with the GIS
        extension enabled.

        ``format_url`` is a URL string containing '%s' where the page name to
        request will be interpolated. For example: 'http://www.wiki.com/wiki/%s'

        ``transform_string`` is a callable that will make appropriate
        replacements to the input string before requesting the page. If None is
        given, the default transform_string which replaces ' ' with '_' will be
        used. It is recommended that you consider this argument keyword-only,
        since subclasses will likely place it last.
        """
        self.format_url = format_url

        if callable(transform_string):
            self.transform_string = transform_string

    @classmethod
    def transform_string(cls, string):
        """Do the WikiMedia dance: replace spaces with underscores."""
        return string.replace(' ', '_')

    def geocode(self, string):
        wiki_string = self.transform_string(string)
        url = self.format_url % wiki_string
        return self.geocode_url(url)

    def geocode_url(self, url):
        print "Fetching %s..." % url
        page = urlopen(url)
        name, (latitude, longitude) = self.parse_xhtml(page)
        return (name, (latitude, longitude))        

    def parse_xhtml(self, page):
        soup = isinstance(page, BeautifulSoup) and page or BeautifulSoup(page)

        meta = soup.head.find('meta', {'name': 'geo.placename'})
        name = meta and meta['content'] or None

        meta = soup.head.find('meta', {'name': 'geo.position'})
        if meta:
            position = meta['content']
            latitude, longitude = util.parse_geo(position)
            if latitude == 0 or longitude == 0:
                latitude = longitude = None
        else:
            latitude = longitude = None

        return (name, (latitude, longitude))


class SemanticMediaWiki(MediaWiki):
    def __init__(self, format_url, attributes=None, relations=None,
                 prefer_semantic=False, transform_string=None):
        """Initialize a geocoder that can parse MediaWiki pages with the GIS
        extension enabled, and can follow Semantic MediaWiki relations until
        a geocoded page is found.

        ``attributes`` is a sequence of semantic attribute names that can
        contain geographical coordinates. They will be tried, in order,
        if the page is not geocoded with the GIS extension. A single attribute
        may be passed as a string.
        For example: attributes=['geographical coordinate']
                 or: attributes='geographical coordinate'
        
        ``relations`` is a sequence of semantic relation names that will be
        followed, depth-first in order, until a geocoded page is found. A
        single relation name may be passed as a string.
        For example: relations=['Located in']
                 or: relations='Located in'
        
        ``prefer_semantic`` indicates whether or not the contents of the
        semantic attributes (given by ``attributes``) should be preferred
        over the GIS extension's coordinates if both exist. This defaults to
        False, since making it True will cause every page's RDF to be
        requested when it often won't be necessary.
        """
        base = super(SemanticMediaWiki, self)
        base.__init__(format_url, transform_string)

        if attributes is None:
            self.attributes = []
        elif isinstance(attributes, basestring):
            self.attributes = [attributes]
        else:
            self.attributes = attributes

        if relations is None:
            self.relations = []
        elif isinstance(relations, basestring):
            self.relations = [relations]
        else:
            self.relations = relations
        
        self.prefer_semantic = prefer_semantic

    def transform_semantic(self, string):
        """Normalize semantic attribute and relation names by replacing spaces
        with underscores and capitalizing the result."""
        return string.replace(' ', '_').capitalize()

    def geocode_url(self, url, tried=None):
        if tried is None:
            tried = set()

        print "Fetching %s..." % url
        page = urlopen(url)
        soup = BeautifulSoup(page)
        name, (latitude, longitude) = self.parse_xhtml(soup)
        if None in (name, latitude, longitude) or self.prefer_semantic:
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

    def parse_rdf_link(self, page, mime_type='application/rdf+xml'):
        """Parse the URL of the RDF link from the <head> of ``page``."""
        soup = isinstance(page, BeautifulSoup) and page or BeautifulSoup(page)
        link = soup.head.find('link', rel='alternate', type=mime_type)
        return link and link['href'] or None

    def parse_rdf(self, page):
        if not isinstance(page, basestring):
            page = self._decode_page(page)
        doc = xml.dom.minidom.parseString(page)

        things = {}
        for thing in reversed(doc.getElementsByTagName('smw:Thing')):
            name = thing.attributes['rdf:about'].value
            articles = thing.getElementsByTagName('smw:hasArticle')
            things[name] = articles[0].attributes['rdf:resource'].value

        # ``thing`` should now be the semantic data for the exported page.

        return (things, thing)

    def get_label(self, thing):
        return self._get_first_text(thing, 'rdfs:label')

    def get_attributes(self, thing, attributes=None):
        if attributes is None:
            attributes = self.attributes
        
        for attribute in attributes:
            attribute = self.transform_semantic(attribute)
            for node in thing.getElementsByTagName('attribute:' + attribute):
                value = node.firstChild.nodeValue.strip()
                yield (attribute, value)

    def get_relations(self, thing, relations=None):
        if relations is None:
            relations = self.relations

        for relation in relations:
            relation = self.transform_semantic(relation)
            for node in thing.getElementsByTagName('relation:' + relation):
                resource = node.attributes['rdf:resource'].value
                yield (relation, resource)


class Google(WebGeocoder):
    """Geocoder using the Google Maps API."""
    
    def __init__(self, api_key=None, domain='maps.google.com',
                 resource='maps/geo', format_string='%s', output_format='kml'):
        """Initialize a customized Google geocoder with location-specific
        address information and your Google Maps API key.

        ``api_key`` should be a valid Google Maps API key. It is required for
        the 'maps/geo' resource to work.

        ``domain`` should be a the Google Maps domain to connect to. The default
        is 'maps.google.com', but if you're geocoding address in the UK (for
        example), you may want to set it to 'maps.google.co.uk'.

        ``resource`` is the HTTP resource to give the query parameter.
        'maps/geo' is the HTTP geocoder and is a documented API resource.
        'maps' is the actual Google Maps interface and its use for just
        geocoding is undocumented. Anything else probably won't work.

        ``format_string`` is a string containing '%s' where the string to
        geocode should be interpolated before querying the geocoder.
        For example: '%s, Mountain View, CA'. The default is just '%s'.
        
        ``output_format`` can be 'json', 'xml', 'kml', 'csv', or 'js' and will
        control the output format of Google's response. The default is 'kml'
        since it is supported by both the 'maps' and 'maps/geo' resources. The
        'js' format is the most likely to break since it parses Google's
        JavaScript, which could change. However, it currently returns the best
        results for restricted geocoder areas such as the UK.
        """
        self.api_key = api_key
        self.domain = domain
        self.resource = resource
        self.format_string = format_string
        self.output_format = output_format

    @property
    def url(self):
        domain = self.domain.strip('/')
        resource = self.resource.strip('/')
        return "http://%(domain)s/%(resource)s?%%s" % locals()

    def geocode(self, string, exactly_one=True):
        params = {'q': self.format_string % string,
                  'output': self.output_format.lower(),
                  }
        if self.resource.rstrip('/').endswith('geo'):
            # An API key is only required for the HTTP geocoder.
            params['key'] = self.api_key

        url = self.url % urlencode(params)
        return self.geocode_url(url, exactly_one)

    def geocode_url(self, url, exactly_one=True):
        print "Fetching %s..." % url
        page = urlopen(url)
        
        dispatch = getattr(self, 'parse_' + self.output_format)
        return dispatch(page, exactly_one)

    def parse_xml(self, page, exactly_one=True):
        """Parse a location name, latitude, and longitude from an XML response.
        """
        if not isinstance(page, basestring):
            page = self._decode_page(page)
        try:
            doc = xml.dom.minidom.parseString(page)
        except ExpatError:
            places = []
        else:
            places = doc.getElementsByTagName('Placemark')

        if exactly_one and len(places) != 1:
            raise ValueError("Didn't find exactly one placemark! " \
                             "(Found %d.)" % len(places))
        
        def parse_place(place):
            location = self._get_first_text(place, ['address', 'name']) or None
            points = place.getElementsByTagName('Point')
            point = points and points[0] or None
            coords = self._get_first_text(point, 'coordinates') or None
            if coords:
                longitude, latitude = [float(f) for f in coords.split(',')[:2]]
            else:
                latitude = longitude = None
                _, (latitude, longitude) = self.geocode(location)
            return (location, (latitude, longitude))
        
        if exactly_one:
            return parse_place(places[0])
        else:
            return (parse_place(place) for place in places)

    def parse_csv(self, page, exactly_one=True):
        raise NotImplementedError

    def parse_kml(self, page, exactly_one=True):
        return self.parse_xml(page, exactly_one)

    def parse_json(self, page, exactly_one=True):
        if not isinstance(page, basestring):
            page = self._decode_page(page)
        json = simplejson.loads(page)
        places = json.get('Placemark', [])

        if exactly_one and len(places) != 1:
            raise ValueError("Didn't find exactly one placemark! " \
                             "(Found %d.)" % len(places))

        def parse_place(place):
            location = place.get('address')
            longitude, latitude = place['Point']['coordinates'][:2]
            return (location, (latitude, longitude))
        
        if exactly_one:
            return parse_place(places[0])
        else:
            return (parse_place(place) for place in places)

    def parse_js(self, page, exactly_one=True):
        """This parses JavaScript returned by queries the actual Google Maps
        interface and could thus break easily. However, this is desirable if
        the HTTP geocoder doesn't work for addresses in your country (the
        UK, for example).
        """
        if not isinstance(page, basestring):
            page = self._decode_page(page)

        LATITUDE = r"[\s,]lat:\s*(?P<latitude>-?\d+\.\d+)"
        LONGITUDE = r"[\s,]lng:\s*(?P<longitude>-?\d+\.\d+)"
        LOCATION = r"[\s,]laddr:\s*'(?P<location>.*?)(?<!\\)',"
        ADDRESS = r"(?P<address>.*?)(?:(?: \(.*?@)|$)"
        MARKER = '.*?'.join([LATITUDE, LONGITUDE, LOCATION])
        MARKERS = r"{markers: (?P<markers>\[.*?\]),\s*polylines:"            

        def parse_marker(marker):
            latitude, longitude, location = marker
            location = re.match(ADDRESS, location).group('address')
            latitude, longitude = float(latitude), float(longitude)
            return (location, (latitude, longitude))

        match = re.search(MARKERS, page)
        markers = match and match.group('markers') or ''
        markers = re.findall(MARKER, markers)
       
        if exactly_one:
            if len(markers) != 1:
                raise ValueError("Didn't find exactly one marker! " \
                                 "(Found %d.)" % len(markers))
            
            marker = markers[0]
            return parse_marker(marker)
        else:
            return (parse_marker(marker) for marker in markers)


class Yahoo(WebGeocoder):
    """Geocoder using the Yahoo! Maps API.
    
    Note: The Terms of Use dictate that the stand-alone geocoder may only be
    used for displaying Yahoo! Maps or points on Yahoo! Maps. Lame.

    See the Yahoo! Maps API Terms of Use for more information:
    http://developer.yahoo.com/maps/mapsTerms.html
    """

    def __init__(self, app_id, format_string='%s', output_format='xml'):
        """Initialize a customized Yahoo! geocoder with location-specific
        address information and your Yahoo! Maps Application ID.

        ``app_id`` should be a valid Yahoo! Maps Application ID.

        ``format_string`` is a string containing '%s' where the string to
        geocode should be interpolated before querying the geocoder.
        For example: '%s, Mountain View, CA'. The default is just '%s'.

        ``output_format`` can currently only be 'xml'.
        """
        self.app_id = app_id
        self.format_string = format_string
        self.output_format = output_format.lower()
        self.url = "http://api.local.yahoo.com/MapsService/V1/geocode?%s"

    def geocode(self, string, exactly_one=True):
        params = {'location': self.format_string % string,
                  'output': self.output_format,
                  'appid': self.app_id
                  }
        url = self.url % urlencode(params)
        return self.geocode_url(url, exactly_one)
    
    def geocode_url(self, url, exactly_one=True):
        print "Fetching %s..." % url
        page = urlopen(url)
        
        parse = getattr(self, 'parse_' + self.output_format)
        return parse(page, exactly_one)

    def parse_xml(self, page, exactly_one=True):
        """Parse a location name, latitude, and longitude from an XML response.
        """
        if not isinstance(page, basestring):
            page = self._decode_page(page)
        doc = xml.dom.minidom.parseString(page)
        results = doc.getElementsByTagName('Result')
        
        if exactly_one and len(results) != 1:
            raise ValueError("Didn't find exactly one result! " \
                             "(Found %d.)" % len(results))

        def parse_result(result):
            strip = ", \n"
            address = self._get_first_text(result, 'Address', strip)
            city = self._get_first_text(result, 'City', strip)
            state = self._get_first_text(result, 'State', strip)
            zip = self._get_first_text(result, 'Zip', strip)
            country = self._get_first_text(result, 'Country', strip)
            city_state = self._join_filter(", ", [city, state])
            place = self._join_filter(" ", [city_state, zip])
            location = self._join_filter(", ", [address, place, country])
            latitude = self._get_first_text(result, 'Latitude') or None
            latitude = latitude and float(latitude)
            longitude = self._get_first_text(result, 'Longitude') or None
            longitude = longitude and float(longitude)
            return (location, (latitude, longitude))
    
        if exactly_one:
            return parse_result(results[0])
        else:
            return (parse_result(result) for result in results)


class GeocoderDotUS(WebGeocoder):
    """Geocoder using the United States-only geocoder.us API at
    http://geocoder.us. This geocoder is free for non-commercial purposes,
    otherwise you must register and pay per call. This class supports both free
    and commercial API usage.
    """
    
    def __init__(self, username=None, password=None, format_string='%s',
                 protocol='xmlrpc'):
        """Initialize a customized geocoder.us geocoder with location-specific
        address information and login information (for commercial usage).
        
        if ``username`` and ``password`` are given, they will be used to send
        account information to the geocoder.us API. If ``username`` is given
        and ``password`` is none, the ``getpass` module will be used to
        prompt for the password.
        
        ``format_string`` is a string containing '%s' where the string to
        geocode should be interpolated before querying the geocoder.
        For example: '%s, Mountain View, CA'. The default is just '%s'.
        
        ``protocol`` currently supports values of 'xmlrpc' and 'rest'.
        """
        if username and password is None:
            prompt = "geocoder.us password for %r: " % username
            password = getpass.getpass(prompt)

        self.format_string = format_string
        self.protocol = protocol
        self.username = username
        self.__password = password

    @property
    def url(self):
        domain = "geocoder.us"
        username = self.username
        password = self.__password
        protocol = self.protocol.lower()
        
        if username and password:
            auth = "%s:%s@" % (username, password)
            resource = "member/service/%s/" % protocol
        else:
            auth = ""
            resource = "service/%s/" % protocol

        if protocol not in ['xmlrpc', 'soap']:
            resource += "geocode?%s"

        return "http://%(auth)s%(domain)s/%(resource)s" % locals()

    def geocode(self, string, exactly_one=True):
        dispatch = getattr(self, 'geocode_' + self.protocol)
        return dispatch(string, exactly_one)

    def geocode_xmlrpc(self, string, exactly_one=True):
        proxy = xmlrpclib.ServerProxy(self.url)
        results = proxy.geocode(self.format_string % string)
        
        if exactly_one and len(results) != 1:
            raise ValueError("Didn't find exactly one result! " \
                             "(Found %d.)" % len(results))

        def parse_result(result):
            address = self._join_filter(" ", [result.get('number'),
                                              result.get('prefix'),
                                              result.get('street'),
                                              result.get('type'),
                                              result.get('suffix')])
            city_state = self._join_filter(", ", [result.get('city'),
                                                  result.get('state')])
            place = self._join_filter(" ", [city_state, result.get('zip')])
            location = self._join_filter(", ", [address, place]) or None
            latitude = result.get('lat')
            longitude = result.get('long')
            return (location, (latitude, longitude))
        
        if exactly_one:
            return parse_result(results[0])
        else:
            return (parse_result(result) for result in results)

    def geocode_rest(self, string, exactly_one=True):
        params = {'address': self.format_string % string}
        url = self.url % urlencode(params)
        page = urlopen(url)
        return self.parse_rdf(page, exactly_one)

    def parse_rdf(self, page, exactly_one=True):
        """Parse a location name, latitude, and longitude from an RDF response.
        """
        if not isinstance(page, basestring):
            page = self._decode_page(page)
        doc = xml.dom.minidom.parseString(page)
        points = doc.getElementsByTagName('geo:Point')
        
        if exactly_one and len(points) != 1:
            raise ValueError("Didn't find exactly one point! " \
                             "(Found %d.)" % len(points))
        
        def parse_point(point):
            strip = ", \n"
            location = self._get_first_text(point, 'dc:description', strip)
            location = location or None
            latitude = self._get_first_text(point, 'geo:lat') or None
            latitude = latitude and float(latitude)
            longitude = self._get_first_text(point, 'geo:long') or None
            longitude = longitude and float(longitude)
            return (location, (latitude, longitude))
            
        if exactly_one:
            return parse_point(points[0])
        else:
            return (parse_point(point) for point in points)


class VirtualEarth(WebGeocoder):
    """Geocoder using Microsoft's Windows Live Local web service, powered by
    Virtual Earth.
    
    WARNING: This does not use a published API and can easily break if
    Microsoft changes their JavaScript.
    """
    SINGLE_LOCATION = re.compile(r"AddLocation\((.*?')\)")
    AMBIGUOUS_LOCATION = re.compile(r"UpdateAmbiguousList\(\[(.*?)\]\)")
    AMBIGUOUS_SPLIT = re.compile(r"\s*,?\s*new Array\(")
    STRING_QUOTE = re.compile(r"(?<!\\)'")

    def __init__(self, domain='local.live.com', format_string='%s'):
        self.domain = domain
        self.format_string = format_string

    @property
    def url(self):
        domain = self.domain
        resource = "search.ashx"
        return "http://%(domain)s/%(resource)s?%%s" % locals()

    def geocode(self, string, exactly_one=True):
        params = {'b': self.format_string % string}
        url = self.url % urlencode(params)
        return self.geocode_url(url, exactly_one)

    def geocode_url(self, url, exactly_one=True):
        print "Fetching %s..." % url
        page = urlopen(url)
        return self.parse_javascript(page, exactly_one)

    def parse_javascript(self, page, exactly_one=True):
        if not isinstance(page, basestring):
            page = self._decode_page(page)

        matches = self.SINGLE_LOCATION.findall(page)
        if not matches:
            for match in self.AMBIGUOUS_LOCATION.findall(page):
                places = self.AMBIGUOUS_SPLIT.split(match)
                matches.extend([place for place in places if place])

        if exactly_one and len(matches) != 1:
            raise ValueError("Didn't find exactly one location! " \
                             "(Found %d.)" % len(matches))

        def parse_match(match):
            json = "[%s]" % self.STRING_QUOTE.sub('"', match.strip('()'))
            array = simplejson.loads(json)
            if len(array) == 8:
                location, (latitude, longitude) = array[0], array[5:7]
            else:
                location, latitude, longitude = array[:3]
                
            return (location, (latitude, longitude))

        if exactly_one:
            return parse_match(matches[0])
        else:
            return (parse_match(match) for match in matches)


class GeoNames(WebGeocoder):
    def __init__(self, format_string='%s', output_format='xml'):
        self.format_string = format_string
        self.output_format = output_format

    @property
    def url(self):
        domain = "ws.geonames.org"
        output_format = self.output_format.lower()
        append_formats = {'json': 'JSON'}
        resource = "postalCodeSearch" + append_formats.get(output_format, '')
        return "http://%(domain)s/%(resource)s?%%s" % locals()

    def geocode(self, string, exactly_one=True):
        params = {'placename': string}
        url = self.url % urlencode(params)
        return self.geocode_url(url, exactly_one)

    def geocode_url(self, url, exactly_one=True):
        page = urlopen(url)
        dispatch = getattr(self, 'parse_' + self.output_format)
        return dispatch(page, exactly_one)

    def parse_json(self, page, exactly_one):
        if not isinstance(page, basestring):
            page = self._decode_page(page)
        json = simplejson.loads(page)
        codes = json.get('postalCodes', [])
        
        if exactly_one and len(codes) != 1:
            raise ValueError("Didn't find exactly one code! " \
                             "(Found %d.)" % len(codes))
        
        def parse_code(code):
            place = self._join_filter(", ", [code.get('placeName'),
                                             code.get('countryCode')])
            location = self._join_filter(" ", [place,
                                               code.get('postalCode')]) or None
            latitude = code.get('lat')
            longitude = code.get('lng')
            latitude = latitude and float(latitude)
            longitude = longitude and float(longitude)
            return (location, (latitude, longitude))

        if exactly_one:
            return parse_code(codes[0])
        else:
            return (parse_code(code) for code in codes)

    def parse_xml(self, page, exactly_one):
        if not isinstance(page, basestring):
            page = self._decode_page(page)
        doc = xml.dom.minidom.parseString(page)
        codes = doc.getElementsByTagName('code')
        
        if exactly_one and len(codes) != 1:
            raise ValueError("Didn't find exactly one code! " \
                             "(Found %d.)" % len(codes))

        def parse_code(code):
            place_name = self._get_first_text(code, 'name')
            country_code = self._get_first_text(code, 'countryCode')
            postal_code = self._get_first_text(code, 'postalcode')
            place = self._join_filter(", ", [place_name, country_code])
            location = self._join_filter(" ", [place, postal_code]) or None
            latitude = self._get_first_text(code, 'lat') or None
            longitude = self._get_first_text(code, 'lng') or None
            latitude = latitude and float(latitude)
            longitude = longitude and float(longitude)
            return (location, (latitude, longitude))
        
        if exactly_one:
            return parse_code(codes[0])
        else:
            return (parse_code(code) for code in codes)


__all__ = ['Geocoder', 'MediaWiki', 'SemanticMediaWiki', 'Google', 'Yahoo',
           'GeocoderDotUS', 'VirtualEarth', 'GeoNames']