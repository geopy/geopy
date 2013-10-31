"""
:class:`.LiveAddress` geocoder.
"""

from geopy.geocoders.base import Geocoder
from geopy.util import logger
from geopy.compat import urlencode


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
        self.api = 'https://api.qualifiedaddress.com/street-address'

    def geocode(self, query, exactly_one=True):
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.
        """
        url = self._compose_url(query)
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(self._call_geocoder(url), exactly_one)

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
            self.api,
            "&".join(("=".join(('auth-token', self.auth_token)), urlencode(query)))
    ))

    def _parse_json(self, response, exactly_one=True):
        """
        Parse responses as JSON objects.
        """
        if not len(response):
            return None
        if exactly_one is True:
            return self._format_structured_address(response[0])
        else:
            return [self._format_structured_address(c) for c in response]

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
