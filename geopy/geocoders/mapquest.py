try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json

from urllib import urlencode
from urllib2 import urlopen
from geopy.geocoders.base import Geocoder
from geopy.util import logger, decode_page, join_filter
from geopy import util

class MapQuest(Geocoder):

    def __init__(self, api_key='', format_string='%s'):
        """Initialize a MapQuest geocoder with address information and
           MapQuest API key.
        """
        self.api_key = api_key
        self.format_string = format_string
        self.url = "http://www.mapquestapi.com/geocoding/v1/address"

    def geocode(self, location, exactly_one=True):
        if isinstance(location, unicode):
            location = location.encode('utf-8')
        params = {'location' : location}
        data = urlencode(params)
        page = urlopen(self.url + '?key=' + self.api_key + '&' + data).read()
        return self.parse_json(page, exactly_one)

    def parse_json(self, page, exactly_one=True):
        """Parse display name, latitude, and longitude from an JSON response."""
        if not isinstance(page, basestring):
            page = decode_page(page)
        resources = json.loads(page)
        statuscode = resources.get('info').get('statuscode')
        if statuscode == 403:
            return "Bad API Key"
        resources = resources.get('results')[0].get('locations')

        if exactly_one and len(resources) != 1:
            from warnings import warn
            warn("Didn't find exactly one resource!" + \
                "(Found %d.), use exactly_one=False\n" % len(resources)
            )

        def parse_resource(resource):
            city = resource['adminArea5']
            county = resource['adminArea4']
            state = resource['adminArea3']
            country = resource['adminArea1']
            latLng = resource['latLng']
            latitude, longitude = latLng.get('lat'), latLng.get('lng')

            location = join_filter(", ", [city, county, state,country])
            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)

            return (location, (latitude, longitude))

        if exactly_one:
            return parse_resource(resources[0])
        else:
            return [parse_resource(resource) for resource in resources]

if __name__ == "__main__":
    mq = MapQuest("Dmjtd%7Clu612007nq%2C20%3Do5-50zah")
    print mq.geocode('Mount St. Helens')
    mq = MapQuest("hDmjtd%7Clu612007nq%2C20%3Do5-50zah")
    print mq.geocode('Mount St. Helens')

