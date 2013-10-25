"""
OpenStreetMaps geocoder, contributed by Alessandro Pasotti of ItOpen.
"""

import xml.dom.minidom

from geopy.geocoders.base import Geocoder
from geopy.util import logger
from geopy.compat import json, urlencode
from geopy.exc import ConfigurationError


class Nominatim(Geocoder):
    """
    Nominatim geocoder for OpenStreetMap servers. Documentation at:
        http://wiki.openstreetmap.org/wiki/Nominatim
    """

    def __init__(self, format_string='%s', output_format='json', # pylint: disable=R0913
                        view_box=(-180,-90,180,90), country_bias=None, proxies=None):
        """
        :param string format_string:

        :param string output_format: 'json' or 'xml' output format

        :param tuple view_box: Coordinates to restrict search within.

        :param string country_bias:
        """
        super(Nominatim, self).__init__(format_string, proxies)
        self.country_bias = country_bias
        self.format_string = format_string
        self.output_format = output_format
        self.view_box = view_box
        self.country_bias = country_bias

        if self.output_format and not self.output_format in (['xml', 'json']):
            raise ConfigurationError('if defined, `output_format` must be one of: "json","xml"')

        self.api = "http://nominatim.openstreetmap.org/search"
        self.reverse_api = " http://nominatim.openstreetmap.org/reverse"

    def geocode(self, query, exactly_one=True):
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.
        """
        super(Nominatim, self).geocode(query)
        params = {
            'q': self.format_string % query,
            'view_box' : self.view_box,
            'format' : self.output_format,
        }

        if self.country_bias:
            params['countrycodes'] = self.country_bias

        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self.parse_json(self._call_geocoder(url), exactly_one)

    def reverse(self, query, exactly_one=True):
        """
        Returns a reverse geocoded location.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param bool exactly_one: Return one result or a list of results, if
            available.
        """
        lat, lng = self._coerce_point_to_string(query).split(',') # doh
        params = {
                'lat': lat,
                'lon' : lng,
                'format': self.output_format.lower(),
          }

        url = "?".join((self.reverse_api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self.parse_json(self._call_geocoder(url), exactly_one)

    def parse_json(self, page, exactly_one):
        if self.output_format == 'json':
            places = json.loads(page)
        elif self.output_format == 'xml':
            places = xml.dom.minidom.parseString(page).getElementsByTagName('place')
        else:
            raise NotImplementedError()

        if not isinstance (places, list):
            places = [places]
        if not len(places):
            return None

        def parse_code(place):
            if self.output_format == 'xml':
                latitude = place.attributes['lat'].value
                longitude = place.attributes['lon'].value
                placename = place.attributes['display_name'].value
            else:
                latitude = place.get('lat', None)
                longitude = place.get('lon', None)
                placename = place.get('display_name')

            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)
            else:
                return None



            return (placename, (latitude, longitude))

        if exactly_one:
            return parse_code(places[0])
        else:
            return [parse_code(place) for place in places]
