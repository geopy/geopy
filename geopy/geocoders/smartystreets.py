"""
:class:`.LiveAddress` geocoder.
"""

from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT, DEFAULT_SCHEME
from geopy.compat import urlencode
from geopy.location import Location
from geopy.exc import GeocoderQuotaExceeded
from geopy.util import logger


class LiveAddress(Geocoder): # pylint: disable=W0223
    """
    Initialize a customized LiveAddress geocoder provided by SmartyStreets.
    More information regarding the LiveAddress API can be found here:
        https://smartystreets.com/products/liveaddress-api
    """
    def __init__(self, auth_token, auth_id, candidates=1, scheme=DEFAULT_SCHEME, # pylint: disable=R0913
                        timeout=DEFAULT_TIMEOUT, proxies=None):
        """
        Initialize a customized SmartyStreets LiveAddress geocoder.


        :param string auth_token: Valid authentication token. Tokens can be
            administered here:
                https://smartystreets.com/account/keys/secret
                
        :param string auth_id: Valid authentication id. Ids can be
            administered here:
                https://smartystreets.com/account/keys/secret

        :param int candidates: An integer between 1 and 10 indicating the max
            number of candidate addresses to return if a valid address
            could be found.

        :param string scheme: Use 'https' or 'http' as the API URL's scheme.
            Default is https. Note that SSL connections' certificates are not
            verified.

            .. versionadded:: 0.97

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising an :class:`geopy.exc.GeocoderTimedOut`
            exception.

            .. versionadded:: 0.97

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

            .. versionadded:: 0.96
        """
        super(LiveAddress, self).__init__(scheme=scheme, timeout=timeout, proxies=proxies)
        self.auth_token = auth_token
        self.auth_id = auth_id
        if candidates:
            if not 1 <= candidates <= 10:
                raise ValueError('candidates must be between 1 and 10')
        self.candidates = candidates
        self.api = '%s://api.smartystreets.com/street-address' % self.scheme

    def geocode(self, street, city=None, state=None, zipcode=None, lastline=None, exactly_one=True):
        """
        Geocode a location query.

        :param string street: street address OR SINGLE LINE FREEFORM ADDRESS
        :param string city: city name if using component address
        :param string state: state name or initials if using component address
        :param string zipcode: ZIP code if using component address
        :param string lastline: combination of city/state/zip if using component address

        :param bool exactly_one: Return one result or a list of results, if
            available.
        """
        
       
        self.street = street
        if city is None:
            self.city = ''
        else:
            self.city = city
            
        if state is None:
            self.state =' '
        else:
            self.state = state
        
        if zipcode is None:
            self.zipcode = ''
        else:
            self.zipcode = zipcode

        if lastline is None:
            self.lastline = ''
        else:
            self.lastline = lastline
            
        if zipcode is None and ((state is not None and city is None) or (state is None and city is not None)):
            print "Incorrect formatting, did not try to geocode"
            return None

        
        
        url = self._compose_url(self.street, self.city, self.state, self.zipcode, self.lastline)
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(self._call_geocoder(url), exactly_one)

    def _geocoder_exception_handler(self, error, message): # pylint: disable=R0201
        """
        LiveStreets-specific exceptions.
        """
        if "no active subscriptions found" in message.lower():
            raise GeocoderQuotaExceeded(message)

    def _compose_url(self, street, city, state, zipcode, lastline):
        query = (
            ('street', street),
            ('city', city),
            ('state', state),
            ('zipcode', zipcode),
            ('lastline', lastline),
            ('candidates', self.candidates)
        )
        
        # don't urlencode the api token
        return '?'.join((
            self.api,
            "&".join(("&".join((
                "=".join(('auth-id', self.auth_id)),
                "=".join(('auth-token', self.auth_token))
                )), urlencode(query)
            ))
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
        latitude = address['metadata'].get('latitude')
        longitude = address['metadata'].get('longitude')
        return Location(
            ", ".join((address['delivery_line_1'], address['last_line'])),
            (latitude, longitude) if latitude and longitude else None,
            address
        )