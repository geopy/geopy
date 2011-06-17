"""
Wrapper to the Yahoo's new PlaceFinder API. (doc says that the API RELEASE 1.0 (22 JUNE 2010))
"""
import xml.dom.minidom
from geopy import util
from geopy import Point
from urllib import urlencode
from urllib2 import urlopen
from geopy.geocoders.base import Geocoder
import simplejson


class Yahoo(Geocoder):

    BASE_URL = "http://where.yahooapis.com/geocode?%s"

    def __init__(self, app_id, format_string='%s', output_format='xml'):
        # output_format could be 'xml' or 'json', 
        # Yahoo API supports serialized PHP too, but not yet supported in this library
        self.appid = app_id
        self.output_format = output_format

    def geocode(self, string, exactly_one=True):
        params = {'location': string,
                  'appid': self.appid
                 }
        if self.output_format == 'json':  
            params['flags'] = 'J'
        url = self.BASE_URL % urlencode(params)
        util.logger.debug("Fetching %s..." % url)
        try:
            return self.geocode_url(url, exactly_one)
        except httplib.BadStatusLine:
            util.logger.debug('ERR_EMPTY_RESPONSE: Server sent no data')
            raise

    def geocode_url(self, url, exactly_one=True):
        page = urlopen(url)
        parse = getattr(self, 'parse_' + self.output_format)
        return parse(page, exactly_one)
    
    def parse_xml(self, page, exactly_one=True):
        if not isinstance(page, basestring):
            page = util.decode_page(page)

        doc = xml.dom.minidom.parseString(page)
        results = doc.getElementsByTagName('ResultSet')[0].getElementsByTagName('Result')

        #if exactly_one and len(results) != 1:
        #    raise ValueError("Didn't find exactly one place! " \
        #                     "(Found %d.)" % len(results))
        
        if not results:
            raise ValueError("No results found")

        def parse_result(result):
            strip = ", \n"
            line1= util.get_first_text(result, 'line1', strip)
            line2 = util.get_first_text(result, 'line2', strip)
            line3 = util.get_first_text(result, 'line3', strip)
            line4 = util.get_first_text(result, 'line4', strip)
            address = util.join_filter(", ", [line1, line2, line3, line4])
            city = util.get_first_text(result, 'city', strip)
            state = util.get_first_text(result, 'state', strip)
            zip = util.get_first_text(result, 'uzip', strip)
            country = util.get_first_text(result, 'country', strip)
            city_state = util.join_filter(", ", [city, state])
            place = util.join_filter(" ", [city_state, zip])
            location = util.join_filter(", ", [address, place, country])
            latitude = util.get_first_text(result, 'latitude') or None
            longitude = util.get_first_text(result, 'longitude') or None
            if latitude and longitude:
                point = Point(latitude, longitude)
            else:
                point = None
            return (location, (latitude, longitude))

        if exactly_one:
            return parse_result(results[0])
        else:
            return [parse_result(result) for result in results]

    def parse_json(self, page, exactly_one=True):
        if not isinstance(page, basestring):
            page = util.decode_page(page)
        json = simplejson.loads(page)
        results = json.get('ResultSet', []).get('Results', [])

        #if (exactly_one and len(results) != 1) and (not reverse):
        #    raise ValueError("Didn't find exactly one placemark! " \
        #                     "(Found %d.)" % len(results))
        if not results:
            raise ValueError("No results found")

        def parse_result(p):
            line1, line2, line3, line4 = p.get('line1'), p.get('line2'), p.get('line3'), p.get('line4')
            address = util.join_filter(", ", [line1, line2, line3, line4])
            city = p.get('city')
            state = p.get('state')
            country = p.get('country')
            location = util.join_filter(", ", [address, city, country])
            lat, lng = p.get('latitude'), p.get('longitude')
            if lat and lng:
                point = Point(lat, lng)
            else:
                point = None
            return (location, (lat, lng))
    
        if exactly_one:
            return parse_result(results[0])
        else:
            return [parse_result(result) for result in results]

    def reverse(self, coord, exactly_one=True):
        (lat, lng) = coord
        params = {'location': '%s,%s' % (lat, lng),
                  'gflags' : 'R',
                  'appid': self.appid
                 }
        if self.output_format == 'json':  
            params['flags'] = 'J'
        url = self.BASE_URL % urlencode(params)
        return self.geocode_url(url, exactly_one)
