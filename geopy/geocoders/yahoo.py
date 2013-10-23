"""
Wrapper to the Yahoo's new PlaceFinder API. (doc says that the API RELEASE
1.0 (22 JUNE 2010))
"""

from geopy import util
from urllib import urlencode
from urllib2 import urlopen
from geopy.geocoders.base import Geocoder
from geopy.util import json


class Yahoo(Geocoder):
    """
    Yahoo... how is this different from .placefinder.YahooPlaceFinder?
    """

    def __init__(self, app_id, format_string=None, output_format=None):
        super(Yahoo, self).__init__(format_string)
        self.app_id = app_id
        self.format_string = format_string
        self.url = "http://where.yahooapis.com/geocode?%s"

        if output_format != None:
            from warnings import warn
            warn('geopy.geocoders.yahoo.Yahoo: The `output_format`'
                    'parameter is deprecated and now ignored. JSON will be '
                    'used internally.', DeprecationWarning)

    def geocode(self, string, exactly_one=True):
        if isinstance(string, unicode):
            string = string.encode('utf-8')
        params = {'location': self.format_string % string,
                  'appid': self.app_id,
                  'flags': 'J'
                 }
        url = self.url % urlencode(params)
        util.logger.debug("Fetching %s...", url)
        return self.geocode_url(url, exactly_one)

    def geocode_url(self, url, exactly_one=True):
        page = urlopen(url)
        return self.parse_json(page, exactly_one)

    def parse_json(self, page, exactly_one=True):
        if not isinstance(page, basestring):
            page = util.decode_page(page)
        doc = json.loads(page)
        results = doc.get('ResultSet', []).get('Results', [])

        if not results:
            raise ValueError("No results found")
        elif exactly_one and len(results) != 1:
            raise ValueError("Didn't find exactly one placemark! " \
                             "(Found %d.)" % len(results))

        def parse_result(place):
            address = util.join_filter(
                ", ",
                [place.get('line1'), place.get('line2'),
                place.get('line3'), place.get('line4')]
            )
            city = place.get('city')
            state = place.get('state')
            country = place.get('country')
            location = util.join_filter(", ", [address, city, state, country])
            lat, lng = place.get('latitude'), place.get('longitude')
            #if lat and lng:
            #    point = Point(floatlat, lng)
            #else:
            #    point = None
            return (location, (float(lat), float(lng)))

        if exactly_one:
            return parse_result(results[0])
        else:
            return [parse_result(result) for result in results]

    def reverse(self, coord, exactly_one=True):
        (lat, lng) = coord
        params = {'location': '%s,%s' % (lat, lng),
                  'gflags' : 'R',
                  'appid': self.app_id,
                  'flags': 'J'
                 }
        url = self.url % urlencode(params)
        return self.geocode_url(url, exactly_one)
