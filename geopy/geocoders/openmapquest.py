"""
:class:`.OpenMapQuest` geocoder.
"""

from geopy.compat import urlencode

from geopy.geocoders.base import Geocoder
from geopy.util import logger


class OpenMapQuest(Geocoder): # pylint: disable=W0223
    """
    Geocoder using MapQuest Open Platform Web Services. Documentation at:
        http://developer.mapquest.com/web/products/open/geocoding-service
    """

    def __init__(self, api_key=None, format_string=None, proxies=None):
        """
        Initialize an Open MapQuest geocoder with location-specific
        address information, no API Key is needed by the Nominatim based
        platform.

        :param string format_string: String containing '%s' where
            the string to geocode should be interpolated before querying
            the geocoder. For example: '%s, Mountain View, CA'. The default
            is just '%s'.
        """
        super(OpenMapQuest, self).__init__(format_string, proxies)

        self.api_key = api_key or ''
        self.api = "http://open.mapquestapi.com/nominatim/v1/search" \
                    "?format=json&%s"

    def geocode(self, query, exactly_one=True): # pylint: disable=W0221
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.
        """
        params = {
            'q': self.format_string % query
        }
        if exactly_one:
            params['maxResults'] = 1
        url = self.api % urlencode(params)
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)

        return self._parse_json(self._call_geocoder(url), exactly_one)

    @classmethod
    def _parse_json(cls, resources, exactly_one=True):
        """
        Parse display name, latitude, and longitude from an JSON response.
        """
        if not len(resources): # pragma: no cover
            return None
        if exactly_one:
            return cls.parse_resource(resources[0])
        else:
            return [cls.parse_resource(resource) for resource in resources]

    @classmethod
    def parse_resource(cls, resource):
        """
        Return location and coordinates tuple from dict.
        """
        location = resource['display_name']

        latitude = resource['lat'] or None
        longitude = resource['lon'] or None
        if latitude and longitude:
            latitude = float(latitude)
            longitude = float(longitude)

        return (location, (latitude, longitude))
