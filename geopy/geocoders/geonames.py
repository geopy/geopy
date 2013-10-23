"""
:class:`GeoNames` geocoder.
"""

from urllib import urlencode
from urllib2 import urlopen

from geopy.geocoders.base import Geocoder
from geopy.util import logger, decode_page
from geopy.compat import json
from geopy import exc


class GeoNames(Geocoder): # pylint: disable=W0223
    """
    GeoNames geocoder, documentation at:
        http://www.geonames.org/export/geonames-search.html

    Reverse geocoding also available, but not yet implemented. Documentation at:
        http://www.geonames.org/maps/us-reverse-geocoder.html
    """

    def __init__(self, country_bias=None, username=None):
        super(GeoNames, self).__init__()
        if username == None:
            raise ValueError(
                'No username given, required for api access.  If you do not '
                'have a GeoNames username, sign up here: '
                'http://www.geonames.org/login'
            )
        self.username = username
        self.country_bias = country_bias
        self.api = "http://api.geonames.org/searchJSON"

    def geocode(self, string, exactly_one=True): # pylint: disable=W0221
        if isinstance(string, unicode): # TODO py3k
            string = string.encode('utf-8')
        params = {
            'q': string,
            'username': self.username
        }
        if self.country_bias:
            params['countryBias'] = self.country_bias
        if exactly_one is True:
            params['maxRows'] = 1
        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self.geocode_url(url, exactly_one)

    def geocode_url(self, url, exactly_one=True):
        page = urlopen(url)
        return self.parse_json(page, exactly_one)


    def parse_json(self, page, exactly_one):
        """
        Parse JSON response body.
        """
        if not isinstance(page, basestring):
            page = decode_page(page)

        doc = json.loads(page)
        places = doc.get('geonames', [])
        err = doc.get('status', None)
        if err and 'message' in err:
            if err['message'].startswith("user account not enabled to use"):
                raise exc.GeocoderInsufficientPrivileges(err['message'])
            else:
                raise exc.GeocoderError(err['message'])
        if not places:
            return None

        def parse_code(place):
            latitude = place.get('lat', None)
            longitude = place.get('lng', None)
            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)
            else:
                return None

            placename = place.get('name')
            state = place.get('adminCode1', None)
            country = place.get('countryCode', None)

            location = ', '.join(
                [x for x in [placename, state, country] if x]
            )

            return (location, (latitude, longitude))

        if exactly_one:
            return parse_code(places[0])
        else:
            return [parse_code(place) for place in places]
