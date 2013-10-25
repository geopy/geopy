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
    def __init__(self, auth_token, candidates=None, proxies=None):
        super(LiveAddress, self).__init__(proxies=proxies)
        self.auth_token = auth_token
        if candidates:
            if not (1 <= candidates <= 10):
                raise ValueError('candidates must be between 1 and 10')
        self.candidates = candidates or 1
        self.url = 'https://api.qualifiedaddress.com/street-address'

    def geocode(self, query, exactly_one=True):
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.
        """
        super(LiveAddress, self).geocode(query)
        url = self._compose_url(query)
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        request = self._execute_request(url)
        response = request.read()
        return self._parse_json(response, exactly_one)

    def _compose_url(self, location):
        """
        Generate API URL.
        """
        query = {

            'street': location,
            'candidates': self.candidates
        }
        # don't urlencode the api token
        return '?'.join((
            self.url,
            "&".join(("=".join(('auth-token', self.auth_token)), urllib.urlencode(query)))
    ))

    def _execute_request(self, url):
        """
        Call API.
        """
        try:
            return self.urlopen(url)
        except urllib2.HTTPError as error:
            raise LiveAddressError(error.getcode(), error.message or error.msg)

    def _parse_json(self, response, exactly_one=True):
        """
        Parse responses as JSON objects.
        """
        candidates = json.loads(response)
        if not len(candidates):
            return None
        if exactly_one is True:
            return self._format_structured_address(candidates[0])
        else:
            return [self._format_structured_address(c) for c in candidates]

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
