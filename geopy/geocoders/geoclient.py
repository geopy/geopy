"""
:class:`.Geoclient` geocoder.
"""

from geopy.compat import urlencode
from geopy.location import Location
from geopy.util import logger
from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT, DEFAULT_SCHEME

from geopy.exc import ConfigurationError


__all__ = ("Geoclient", )

DEFAULT_ENDPOINT = 'api.cityofnewyork.us/geoclient'
DEFAULT_ENDPOINT_VERSION = 'v1'

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
            scheme=DEFAULT_SCHEME,
            domain=DEFAULT_ENDPOINT + '/' + DEFAULT_ENDPOINT_VERSION,
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
            user_agent=None,
    ):
        """
        Initialize Geoclient geocoder. Please note that 'scheme' parameter is
        not supported: at present state, all Geoclient traffic use https.

        :param string app_id: The application ID.

        :param string app_key: The application key. 

        :param string domain: Currently it is 'api.cityofnewyork.us/geoclient/v1', can
            be changed if you have an on-premise Geoclient instance.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

        """
        super(Geoclient, self).__init__(
            scheme=scheme, timeout=timeout, proxies=proxies, user_agent=user_agent
        )

        self.app_id = app_id
        self.app_key = app_key
        self.domain = domain.strip('/')
        self.scheme = scheme

        if app_id or app_key or domain.startswith(DEFAULT_ENDPOINT):
            if not (app_id and app_key and domain.startswith(DEFAULT_ENDPOINT) ):
                raise ConfigurationError(
                    'app_id and app_key required for NYC Geoclient API access. '
                    'If you don not have a Geoclient access, sign up here: '
                    'https://developer.cityofnewyork.us/api/geoclient-api'
                )
            if self.scheme != 'https':
                raise ConfigurationError(
                    "Authenticated mode requires scheme of 'https'"
                )
        
        '''use SFS (Single-field search) endpoint'''
        self.geocode_api = '%s://%s/search.json' % (self.scheme, self.domain)


    def geocode(
            self,
            query,
            exactly_one=True,
            timeout=None,
            detailsCSV=None,
            addressdetails=False,
        ):
        """
        Geocode a location query.

        :param string query: The query string to be geocoded using SFS syntax.  
            Documentation at:
            https://api.cityofnewyork.us/geoclient/v1/doc#section-1.3

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param string detailsCSV: Comma-delimited list of additional details to append to location
            as a comma-delimited list as well. For example, "nta, electionDistrict, communityDistrict"
            for the address "85 Fifth Ave, NY, NY" appends "(nta:MN13, electionDistrict:008, communityDistrict:105)"
            to location.  Case sensitive. For valid values, see:
            https://api.cityofnewyork.us/geoclient/v1/doc#section-3.0
            

        :param bool addressdetails: If you want in *Location.raw* to include the entire
            Geoclient JSON response and not just select details (see detailsCSV), set this to True.
            Data Dictionary documenting all available fields at:
            https://api.cityofnewyork.us/geoclient/v1/doc#section-3.0

        """
        params = {
            'input': self.format_string % query,
            'app_key': self.app_key,
            'app_id': self.app_id,
        }

        url = "?".join((self.geocode_api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json_geocode(
            self._call_geocoder(url, timeout=timeout), exactly_one, detailsCSV, addressdetails
        )


    @staticmethod
    def _parse_json_geocode(page, exactly_one=True, detailsCSV=None, addressdetails=False):
        '''Returns location from Geoclient response.'''

        places = page['results']

        if not len(places):
            return None

        def parse_place(place):
            '''Get the location, lat, lon from a single json result.'''
            '''Return normalized street address in location, and the entire Geoclient response is also returned'''
            '''if addressdetails is set to true should the user want to parse extended location information'''
            
            request_type = place.get('request').split(' ', 1)[0]
            
            response_info = place['response']
            
            if request_type == 'address':
                location = "".join([response_info.get('houseNumber', ''), ' ', 
                    response_info.get('boePreferredStreetName', ''), ', ', 
                    response_info.get('firstBoroughName', ''), ', NY ', 
                    response_info.get('zipCode', '')])

            else:
                '''for BBL, BIN, BLOCKFACE and INTERSECTION request types, just pass through the request value'''
                location = place.get('request', '')
                
            if request_type == 'bin':
                '''for BIN, return the latlong at the midpoint of the building'''
                latitude = response_info.get('latitudeInternalLabel', None)
                longitude = response_info.get('longitudeInternalLabel', None)
            else:
                latitude = response_info.get('latitude', None)
                longitude = response_info.get('longitude', None)
            
            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)

            if detailsCSV:
                '''if a comma separate list of Geoclient properties are specified,'''
                '''lookup and append the value to location''' 
                propertyInfoList = [propertyInfo.strip() for propertyInfo in detailsCSV.split(',')]
                propertyInfoResults = ['%s:%s' % (propertyInfo, response_info.get(propertyInfo, '')) for propertyInfo in propertyInfoList ]
                location = "".join([location, " (", ", ".join(propertyInfoResults), ")"])
            
            return Location(location, (latitude, longitude), place if addressdetails else {})

        if exactly_one:
            return parse_place(places[0])
        else:
            return [parse_place(place) for place in places]
