"""
:class:`.Bing` geocoder.
"""

from geopy.util import json

from urllib import urlencode
from urllib2 import urlopen

from geopy.geocoders.base import Geocoder
from geopy.util import logger, decode_page, join_filter


class Bing(Geocoder):
    """
    Geocoder using the Bing Maps Locations API. Documentation at:
        http://msdn.microsoft.com/en-us/library/ff701715.aspx
    """

    def __init__(self, api_key, format_string='%s', output_format=None):
        """Initialize a customized Bing geocoder with location-specific
        address information and your Bing Maps API key.

        ``api_key`` should be a valid Bing Maps API key.

        ``format_string`` is a string containing '%s' where the string to
        geocode should be interpolated before querying the geocoder.
        For example: '%s, Mountain View, CA'. The default is just '%s'.

        ``output_format`` (DEPRECATED) is ignored
        """
        super(Bing, self).__init__(format_string)
        if output_format != None:
            from warnings import warn
            warn('geopy.geocoders.bing.Bing: The `output_format` parameter '
                'is deprecated and ignored.', DeprecationWarning)

        self.api_key = api_key
        self.url = "http://dev.virtualearth.net/REST/v1/Locations"

    def geocode(self, string, exactly_one=True, user_location=None): # pylint: disable=W0221
        """Geocode an address.

        ``user_location`` should be an instance of geopy.Point. user_location
        position prioritizes results that are closer to this location.
        """
        if isinstance(string, unicode):
            string = string.encode('utf-8')
        params = {'query': self.format_string % string,
                  'key': self.api_key
                  }

        if user_location:
            params['userLocation'] = "%s,%s" % (
                user_location.latitude, user_location.longitude)

        url = "%s?%s" % (self.url, urlencode(params))
        return self.geocode_url(url, exactly_one)

    def reverse(self, point, exactly_one=True): # pylint: disable=W0221
        """Reverse geocode a point.

        ``point`` should be an instance of geopy.Point.
        """
        params = {'key': self.api_key}

        url = "%s/%s,%s?%s" % (
            self.url, point.latitude, point.longitude, urlencode(params))

        return self.geocode_url(url, exactly_one=exactly_one)

    def geocode_url(self, url, exactly_one=True):
        logger.debug("Fetching %s...", url)
        page = urlopen(url)

        return self.parse_json(page, exactly_one)

    @staticmethod
    def parse_json(page, exactly_one=True):
        """
        Parse a location name, latitude, and longitude from an JSON response.
        """
        if not isinstance(page, basestring):
            page = decode_page(page)
        doc = json.loads(page)
        resources = doc['resourceSets'][0]['resources']

        if exactly_one and len(resources) != 1:
            raise ValueError("Didn't find exactly one resource! " \
                             "(Found %d.)" % len(resources))

        def parse_resource(resource):
            stripchars = ", \n"
            addr = resource['address']

            address = addr.get('addressLine', '').strip(stripchars)
            city = addr.get('locality', '').strip(stripchars)
            state = addr.get('adminDistrict', '').strip(stripchars)
            zipcode = addr.get('postalCode', '').strip(stripchars)
            country = addr.get('countryRegion', '').strip(stripchars)

            city_state = join_filter(", ", [city, state])
            place = join_filter(" ", [city_state, zipcode])
            location = join_filter(", ", [address, place, country])

            latitude = resource['point']['coordinates'][0] or None
            longitude = resource['point']['coordinates'][1] or None
            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)

            return (location, (latitude, longitude))

        if exactly_one:
            return parse_resource(resources[0])
        else:
            return [parse_resource(resource) for resource in resources]
