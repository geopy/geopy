import xml.dom.minidom
from geopy import util
from urllib import urlencode
from urllib2 import urlopen
from geopy.geocoders.base import Geocoder


class Yahoo(Geocoder):

    BASE_URL = "http://api.local.yahoo.com/MapsService/V1/geocode?%s"

    def __init__(self, app_id, format_string='%s', output_format='xml'):
        self.app_id = app_id
        self.format_string = format_string
        self.output_format = output_format.lower()

    def geocode(self, string, exactly_one=True):
        params = {'location': self.format_string % string,
                  'output': self.output_format,
                  'appid': self.app_id
                 }
        url = self.BASE_URL % urlencode(params)
        return self.geocode_url(url, exactly_one)

    def geocode_url(self, url, exactly_one=True):
        util.logger.debug("Fetching %s..." % url)
        page = urlopen(url)

        return self.parse_xml(page, exactly_one)

    def parse_xml(self, page, exactly_one=True):
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
            latitude = float(util.get_first_text(result, 'Latitude')) or None
            longitude = float(util.get_first_text(result, 'Longitude')) or None
            
            # TODO use Point/Location object API in 0.95
            #if latitude and longitude:
            #    point = Point(latitude, longitude)
            #else:
            #    point = Non
            #return Location(location, point, {
            #    'Address': address,
            #    'City': city,
            #    'State': state,
            #    'Zip': zip,
            #    'Country': country
            #})
            
            return address, (latitude, longitude)

        if exactly_one:
            return parse_result(results[0])
        else:
            return [parse_result(result) for result in results]
