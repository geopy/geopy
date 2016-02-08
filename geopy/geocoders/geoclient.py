"""
:class:`.Geoclient` geocoder.
"""

from geopy.compat import urlencode
from geopy.location import Location
from geopy.util import logger
from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT

from geopy.exc import ConfigurationError


__all__ = ("Geoclient", )


class Geoclient(Geocoder):
    """
    Geocoder using the Geoclient API. Documentation at:

        https://api.cityofnewyork.us/geoclient/v1/doc

     to get access, go to:

        https://developer.cityofnewyork.us/api/geoclient-api   
    """

    def __init__(
            self,
            app_id=None,
            app_key=None,
            domain='api.cityofnewyork.us/geoclient/v1',
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
            user_agent=None,
    ):
        """
        Initialize Geoclient geocoder. Please note that 'scheme' parameter is
        not supported: at present state, all Geoclient traffic use https.

        :param string appd_id: The application ID.

        :param string app_key: The application key. 

        :param string domain: Currently it is 'api.cityofnewyork.us/geoclient/v1', can
            be changed if you have an on-premise Geoclient instance.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

        """
        super(Geoclient, self).__init__(
            scheme="https", timeout=timeout, proxies=proxies, user_agent=user_agent
        )

        self.app_id = app_id
        self.app_key = app_key
        
        if not app_id:
            raise ConfigurationError(
                'No app_id given, required for api access.  If you do not '
                'have a Geoclient app_id, sign up here: '
                'https://developer.cityofnewyork.us/api/geoclient-api'
                )
        
        if not app_key:
            raise ConfigurationError(
                'No app_key given, required for api access.  If you do not '
                'have a Geoclient app_key, sign up here: '
                'https://developer.cityofnewyork.us/api/geoclient-api'
                )
        
        self.domain = domain.strip('/')
        
        '''use SFS (Single-field search) endpoint'''
        self.geocode_api = 'https://%s/search.json' % (self.domain)

    def geocode(
            self,
            query,
            exactly_one=True,
            timeout=None,
            addressdetails=False,
        ):
        """
        Geocode a location query.

        :param string query: The query string to be geocoded; this must
            be URL encoded.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param bool addressdetails: If you want in *Location.raw* to include
            addressdetails such as BIN#, community district, etc set it to True

        """
        params = {
            'input': self.format_string % query,
        }

        if self.app_key is not None:
            params["app_key"] = self.app_key

        if self.app_id is not None:
            params["app_id"] = self.app_id

        url = "?".join((self.geocode_api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json_geocode(
            self._call_geocoder(url, timeout=timeout), exactly_one, addressdetails
        )


    @staticmethod
    def _parse_json_geocode(page, exactly_one=True, addressdetails=False):
        '''Returns location from Geoclient response.'''

        places = page['results']

        if not len(places):
            return None

        def parse_place(place):
            '''Get the location, lat, lon from a single json result.'''
            '''Return normalized street address in location, and the entire Geoclient response is also returned'''
            '''should the user want to parse extended location information'''
            location = place.get('houseNumber') + ' ' + place.get('boePreferredStreetName') + ', ' + place.get('firstBoroughName') + ', NY ' + place.get('zipCode')
            latitude = place.get('latitude')
            longitude = place.get('longitude')
            return Location(location, (latitude, longitude), place if addressdetails else {})

        if exactly_one:
            return parse_place(places[0]['response'])
        else:
            return [parse_place(place['response']) for place in places]
