import json
import urllib
import urllib2
from geopy.geocoders.base import Geocoder


LOCATION = 'https://api.qualifiedaddress.com/street-address/'


class LiveAddress(Geocoder):
    """Initialize a customized LiveAddress geocoder provided by SmartyStreets.
    More information regarding the LiveAddress API can be found here:
    http://smartystreets.com/products/liveaddress-api

    ``auth_token`` should be a valid authentication token. This token must
    correspond with an active LiveAddress subscription (see the following page
    to administer your subscriptions: https://smartystreets.com/account).

    ``candidates`` is an integer between 1 and 10 indicating the max number of
    candidate addresses to return if a valid address could be found.
    """
    def __init__(self, auth_token, candidates=1):
        self.auth_token = auth_token
        self.candidates = candidates if 1 <= candidates <= 10 else 10
        super(LiveAddress, self).__init__()

    def geocode(self, location):
        url = self._compose_url(location)
        request = self._execute_request(url)
        response = request.read()
        return self._parse_json(response)

    def _compose_url(self, location):
        query = {
            'auth-token': self.auth_token,
            'street': location,
            'candidates': self.candidates
        }
        return LOCATION + '?' + urllib.urlencode(query)

    def _execute_request(self, url):
        try:
            return urllib2.urlopen(url)
        except urllib2.HTTPError as error:
            raise LiveAddressError(error.getcode(), error.message or error.msg)

    def _parse_json(self, response):
        candidates = json.loads(response)
        if len(candidates) > 1:
            return [self._format_structured_address(c) for c in candidates]

        return self._format_structured_address(candidates[0])

    def _format_structured_address(self, address):
        formatted = '{0}, {1}'.format(
            address['delivery_line_1'],
            address['last_line'])

        metadata = address['metadata']
        latlon = metadata['latitude'], metadata['longitude']
        return formatted, latlon


class LiveAddressError(Exception):
    def __init__(self, http_status, message):
        self.http_status = http_status
        super(Exception, self).__init__(message)