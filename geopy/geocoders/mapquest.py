"""
:class:`.MapQuest` geocoder.
"""

from urllib import urlencode
from urllib2 import urlopen

from geopy.compat import json
from geopy.geocoders.base import Geocoder
from geopy.util import logger, decode_page, join_filter
from geopy import exc


class MapQuest(Geocoder): # pylint: disable=W0223
    """
    MapQuest geocoder, documentation at:
        http://www.mapquestapi.com/geocoding/
    """

    def __init__(self, api_key=None, format_string=None, proxies=None):
        """
        Initialize a MapQuest geocoder with address information and
        MapQuest API key.
        """
        super(MapQuest, self).__init__(format_string, proxies)
        self.api_key = api_key or ''
        self.api = "http://www.mapquestapi.com/geocoding/v1/address"

    def geocode(self, query, exactly_one=True): # pylint: disable=W0221
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.
        """
        super(MapQuest, self).geocode(query)
        params = {
            'key': self.api_key,
            'location' : query
        }
        if exactly_one:
            params['maxResults'] = 1
        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        page = self.urlopen(url).read()
        return self.parse_json(page, exactly_one)

    def parse_json(self, page, exactly_one=True):
        """
        Parse display name, latitude, and longitude from an JSON response.
        """
        if not isinstance(page, basestring):
            page = decode_page(page)
        resources = json.loads(page)
        if resources.get('info').get('statuscode') == 403:
            raise exc.GeocoderAuthenticationFailure()

        # TODO fix len==0
        resources = resources.get('results')[0].get('locations')

        def parse_resource(resource):
            city = resource['adminArea5']
            county = resource['adminArea4']
            state = resource['adminArea3']
            country = resource['adminArea1']
            latLng = resource['latLng']
            latitude, longitude = latLng.get('lat'), latLng.get('lng')

            location = join_filter(", ", [city, county, state, country])
            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)

            return (location, (latitude, longitude))

        if exactly_one:
            return parse_resource(resources[0])
        else:
            return [parse_resource(resource) for resource in resources]

if __name__ == "__main__":
    # TODO test
    mq = MapQuest("Dmjtd%7Clu612007nq%2C20%3Do5-50zah")
    print mq.geocode('Mount St. Helens')
    mq = MapQuest("hDmjtd%7Clu612007nq%2C20%3Do5-50zah")
    print mq.geocode('Mount St. Helens')

