from urllib import urlencode
from urllib2 import urlopen
from geopy import util

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json

from geopy.geocoders.base import Geocoder

class GeoNamesTimezone(Geocoder):
    def __init__(self, username=None):
        self.username = username
        self.url = "http://api.geonames.org/timezoneJSON?%s"
    
    def geocode(self, latitude=None, longitude=None):
        params = {
            'lat': latitude,
            'lng': longitude,
            'username': self.username
        }
        url = self.url % urlencode(params)
        return self.geocode_url(url)

    def geocode_url(self, url):
        page = urlopen(url)
        return self.parse_json(page)

    def parse_json(self, page):
        if not isinstance(page, basestring):
            page = util.decode_page(page)

        doc = json.loads(page)

        return doc.get('timezoneId', None)
