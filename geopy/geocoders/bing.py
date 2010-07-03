import xml.dom.minidom
from urllib import urlencode
from urllib2 import urlopen

from geopy.geocoders.base import Geocoder

class Bing(Geocoder):
    """Geocoder using the Bing Maps API."""

    def __init__(self, api_key, format_string='%s', output_format='xml'):
        """Initialize a customized Bing geocoder with location-specific
        address information and your Bing Maps API key.

        ``api_key`` should be a valid Bing Maps API key.

        ``format_string`` is a string containing '%s' where the string to
        geocode should be interpolated before querying the geocoder.
        For example: '%s, Mountain View, CA'. The default is just '%s'.

        ``output_format`` can currently only be 'xml'.
        """
        self.api_key = api_key
        self.format_string = format_string
        self.output_format = output_format.lower()
        self.url = "http://dev.virtualearth.net/REST/v1/Locations?%s"

    def geocode(self, string, exactly_one=True):
        params = {'addressLine': self.format_string % string,
                  'o': self.output_format,
                  'key': self.api_key
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
        resources = doc.getElementsByTagName('Resources')

        if exactly_one and len(resources) != 1:
            raise ValueError("Didn't find exactly one resource! " \
                             "(Found %d.)" % len(resources))

        def parse_resource(resource):
            strip = ", \n"
            address = self._get_first_text(resource, 'AddressLine', strip)
            city = self._get_first_text(resource, 'Locality', strip)
            state = self._get_first_text(resource, 'AdminDistrict', strip)
            zip = self._get_first_text(resource, 'PostalCode', strip)
            country = self._get_first_text(resource, 'CountryRegion', strip)
            city_state = self._join_filter(", ", [city, state])
            place = self._join_filter(" ", [city_state, zip])
            location = self._join_filter(", ", [address, place, country])
            latitude = self._get_first_text(resource, 'Latitude') or None
            latitude = latitude and float(latitude)
            longitude = self._get_first_text(resource, 'Longitude') or None
            longitude = longitude and float(longitude)

            return (location, (latitude, longitude))

        if exactly_one:
            return parse_resource(resources[0])
        else:
            return (parse_resource(resource) for resource in resources)
