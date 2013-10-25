# OSM geocoder
# See: http://wiki.openstreetmap.org/wiki/Nominatim
# Author: Alessandro Pasotti (ItOpen)
# URL: http://www.itopen.it
# Licence: AGPL
# Date: 2011-12-20


try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json

from geopy.geocoders.base import Geocoder
from geopy.util import logger, decode_page
from geopy.point import Point
from urllib import urlencode
from urllib2 import urlopen


class Nominatim(Geocoder):
    def __init__(self, api_key=None, format_string='%s', output_format='json', view_box=(-180,-90,180,90), country_bias=None):

        self.country_bias = country_bias
        self.format_string = format_string
        self.output_format = output_format
        self.view_box = view_box
        self.country_bias = country_bias

        if self.output_format and not self.output_format in (['xml', 'json']):
            raise ValueError('if defined, `output_format` must be one of: "json","xml"')

        self.url = "http://nominatim.openstreetmap.org/search?%s"
        self.reverse_url = " http://nominatim.openstreetmap.org/reverse?%s"

    def geocode(self, string, exactly_one=True):
        params = {
            'q': self.format_string % string,
            'view_box' : self.view_box,
            'format' : self.output_format,
        }

        if self.country_bias:
            params['countrycodes'] = self.country_bias

        url = self.url % urlencode(params)
        return self.geocode_url(url, exactly_one)

    def geocode_url(self, url, exactly_one=True, reverse=False):
        logger.debug("Fetching %s..." % url)
        page = urlopen(url)
        return self.parse_json(page, exactly_one)

    def reverse(self, coord, exactly_one=True):
        if isinstance(coord, Point):
            (lat, lng, _) = coord
        else:
            (lat, lng) = coord

        params = {
                'lat': lat,
                'lon' : lng,
                'format': self.output_format.lower(),
          }

        url = self.reverse_url % urlencode(params)
        return self.geocode_url(url, exactly_one, reverse=True)

    def parse_json(self, page, exactly_one):
        if not isinstance(page, basestring):
            page = decode_page(page)

        doc = json.loads(page)
        places = doc

        if not isinstance (places, list):
            places = [places]

        if not places:
            return None

        if exactly_one and len(places) != 1:
            raise ValueError("Didn't find exactly one code! " \
                             "(Found %d.)" % len(places))

        def parse_code(place):
            latitude = place.get('lat', None)
            longitude = place.get('lon', None)
            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)
            else:
                return None

            placename = place.get('display_name')

            return (placename, (latitude, longitude))

        if exactly_one:
            return parse_code(places[0])
        else:
            return [parse_code(place) for place in places]