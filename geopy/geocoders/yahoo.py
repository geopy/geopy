import xml.dom.minidom
from geopy import util
from geopy import Point, Location
from urllib import urlencode
from urllib2 import urlopen, HTTPError
from geopy.geocoders.base import Geocoder


class Yahoo(Geocoder):

    BASE_URL = "http://api.local.yahoo.com/MapsService/V1/geocode?%s"

    def __init__(self, app_id, format_string='%s', output_format='xml'):
        self.app_id = app_id
        self.format_string = format_string
        self.output_format = output_format.lower()

    def geocode(self, string):
        params = {'location': self.format_string % string,
                  'output': self.output_format,
                  'appid': self.app_id
                 }
        url = self.BASE_URL % urlencode(params)
        return self.geocode_url(url)

    def geocode_url(self, url):
        print "Fetching %s..." % url
        page = urlopen(url)

        parse = getattr(self, 'parse_' + self.output_format)
        return parse(page)

    def parse_xml(self, page):
        if not isinstance(page, basestring):
            page = util.decode_page(page)

        doc = xml.dom.minidom.parseString(page)
        results = doc.getElementsByTagName('Result')

        def parse_result(result):
            strip = ", \n"
            address = util.get_first_text(result, 'Address', strip)
            city = util.get_first_text(result, 'City', strip)
            state = util.get_first_text(result, 'State', strip)
            zip = util.get_first_text(result, 'Zip', strip)
            country = util.get_first_text(result, 'Country', strip)
            city_state = util.join_filter(", ", [city, state])
            place = util.join_filter(" ", [city_state, zip])
            location = util.join_filter(", ", [address, place, country])
            latitude = util.get_first_text(result, 'Latitude') or None
            longitude = util.get_first_text(result, 'Longitude') or None
            if latitude and longitude:
                point = Point(latitude, longitude)
            else:
                point = Non
            return Location(location, point, {
                'Address': address,
                'City': city,
                'State': state,
                'Zip': zip,
                'Country': country
            })

        return [parse_result(result) for result in results]
