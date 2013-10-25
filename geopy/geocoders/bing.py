"""
:class:`.Bing` geocoder.
"""

from geopy.compat import json

from urllib import urlencode
from urllib2 import urlopen

from geopy.geocoders.base import Geocoder
from geopy.util import logger, decode_page, join_filter


class Bing(Geocoder):
    """
    Geocoder using the Bing Maps Locations API. Documentation at:
        http://msdn.microsoft.com/en-us/library/ff701715.aspx
    """

    def __init__(self, api_key, format_string=None):
        """Initialize a customized Bing geocoder with location-specific
        address information and your Bing Maps API key.

        :param string api_key: should be a valid Bing Maps API key.

        :param string format_string: is a string containing '%s' where the
            string to geocode should be interpolated before querying the
            geocoder. For example: '%s, Mountain View, CA'. The default
            is just '%s'.
        """
        super(Bing, self).__init__(format_string)
        self.api_key = api_key
        self.api = "http://dev.virtualearth.net/REST/v1/Locations"

    def geocode(self, query, exactly_one=True, user_location=None): # pylint: disable=W0221
        """
        Geocode an address.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param user_location: Prioritize results closer to
            this location.

            .. versionadded:: 0.96.0

        :type user_location: :class:`geopy.point.Point`
        """
        super(Bing, self).geocode(query)
        params = {
            'query': self.format_string % query,
            'key': self.api_key
        }
        if user_location:
            params['userLocation'] = ",".join(
                (user_location.latitude, user_location.longitude)
            )
        if exactly_one is True:
            params['maxResults'] = 1

        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self.geocode_url(url, exactly_one)

    def reverse(self, point, exactly_one=True): # pylint: disable=W0221
        """
        Reverse geocode a point.

        :param point: Location which you would like an address for.
        :type point: :class:`geopy.point.Point`

        :param bool exactly_one: Return one result, or a list?
        """
        params = {'key': self.api_key}
        url = "%s/%s,%s?%s" % (
            self.api, point.latitude, point.longitude, urlencode(params))

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self.geocode_url(url, exactly_one=exactly_one)

    def geocode_url(self, url, exactly_one=True):
        """
        Geocode a given URL, rather than having the class construct the call.
        """
        logger.debug("%s.geocode_url: %s", self.__class__.__name__, url)
        return self.parse_json(urlopen(url), exactly_one)

    @staticmethod
    def parse_json(page, exactly_one=True):
        """
        Parse a location name, latitude, and longitude from an JSON response.
        """
        if not isinstance(page, basestring):
            page = decode_page(page)
        doc = json.loads(page)
        resources = doc['resourceSets'][0]['resources']

        def parse_resource(resource):
            """
            Parse each return object.
            """
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
