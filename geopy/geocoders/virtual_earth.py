import re
from urllib2 import urlopen
from urllib import urlencode
import simplejson
from geopy.geocoders.base import Geocoder
from geopy.point import Point
from geopy.location import Location
from geopy import util

class VirtualEarth(Geocoder):
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
            page = util.decode_page(page)

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