"""
:class:`.LiveAddress` geocoder.
"""

import json
import urllib
import urllib2

from geopy.geocoders.base import Geocoder
from geopy.util import logger


class LiveAddress(Geocoder): # pylint: disable=W0223
    """
    Initialize a customized LiveAddress geocoder provided by SmartyStreets.
    More information regarding the LiveAddress API can be found here:
    http://smartystreets.com/products/liveaddress-api

    ``auth_token`` should be a valid authentication token.  Tokens can be
    administered from here:
        https://smartystreets.com/account/keys/secret

    The token you use must correspond with an active LiveAddress subscription
    Subscriptions can be administered here:
        https://smartystreets.com/account/subscription

    ``candidates`` is an integer between 1 and 10 indicating the max number of
    candidate addresses to return if a valid address could be found.
    """
    def __init__(self, auth_id, auth_token, candidates=None):
        super(LiveAddress, self).__init__()
        self.auth_id = auth_id
        self.auth_token = auth_token
        if candidates:
            if not (1 <= candidates <= 10):
                raise ValueError('candidates must be between 1 and 10')
        self.candidates = candidates or 1
        self.url = 'https://api.qualifiedaddress.com/street-address'

    def geocode(self, query):
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.
        """
        super(LiveAddress, self).geocode(query)
        url = self._compose_url(query)
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        request = self._execute_request(url)
        response = request.read()
        return self._parse_json(response)

    def _compose_url(self, location):
        """
        Generate API URL.
        """
        query = {
            'auth-id': self.auth_id,
            'auth-token': self.auth_token,
            'street': location,
            'candidates': self.candidates
        }
        return '?'.join((self.url, urllib.urlencode(query)))

    @staticmethod
    def _execute_request(url):
        """
        Call API.
        """
        try:
            return urllib2.urlopen(url)
        except urllib2.HTTPError as error:
            raise LiveAddressError(error.getcode(), error.message or error.msg)

    def _parse_json(self, response):
        """
        Parse responses as JSON objects.
        """
        candidates = json.loads(response)
        if len(candidates) > 1:
            return [self._format_structured_address(c) for c in candidates]

        return self._format_structured_address(candidates[0])

    @staticmethod
    def _format_structured_address(address):
        """
        Pretty-print address and return lat, lon tuple.
        """
        formatted = '{0}, {1}'.format(
            address['delivery_line_1'],
            address['last_line'])

        metadata = address['metadata']
        latlon = metadata['latitude'], metadata['longitude']
        return formatted, latlon


class LiveAddressError(Exception):
    """
    TODO generalize.
    """
    def __init__(self, http_status, message):
        self.http_status = http_status
        super(LiveAddressError, self).__init__(message)
