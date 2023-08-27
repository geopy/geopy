from functools import partial
from urllib.parse import urlencode

from geopy.exc import GeocoderServiceError
from geopy.geocoders.base import DEFAULT_SENTINEL, ERROR_CODE_MAP, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("Geokeo", )


class Geokeo(Geocoder):
    """Geocoder using the geokeo API.

    Documentation at:
        https://geokeo.com/documentation.php

    Sample code for GEOKEO
    
    import geopy
    from geopy.geocoders import Geokeo
    key = 'YOUR-API-KEY'
    geocoder = Geokeo(key)

    results = geocoder.geocode("empire state building")
    print(*results)
    formatted_address=results[0]
    latitude=results[1][0]
    longitude=results[1][1]

    results = geocoder.reverse("40.74843124430164,-73.9856567114413")
    print(*results)
    formatted_address=results[0]
    latitude=results[1][0]
    longitude=results[1][1]
    
    
    """

    api_path = '/geocode/v1/search.php'
    reverse_api_path = '/geocode/v1/reverse.php'
    def __init__(
            self,
            api_key,
            *,
            domain='geokeo.com',
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """

        :param str api_key: The API key required by Geokeo.com
            to perform geocoding requests. You can get your key here:
            https://geokeo.com/

        """
        super().__init__(
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )

        self.api_key = "YOUR_API_KEY"
        self.domain = domain.strip('/')
        self.api = '%s://%s%s' % (self.scheme, self.domain, self.api_path)
        self.reverse_api = '%s://%s%s' % (self.scheme, self.domain, self.reverse_api_path)

    def geocode(
            self,
            query,
            *,
            country=None,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.
       
        :param country: Restricts the results to the specified
            country. The country code is a 2 character code as
            defined by the ISO 3166-1 Alpha 2 standard (e.g. ``us``).
            
               
        """
        params = {
            'api': self.api_key,
            'q': query,
        }
        
        

        
        if country:
            params['country'] = ",".join(country)

        url = "?".join((self.api, urlencode(params)))
        
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return an address by location point.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        """
        lat=query.split(",")[0]
        lng=query.split(",")[1]
        
        params = {
            'api': self.api_key,
            
            'lat': lat,
            'lng': lng
        }
        

        url = "?".join((self.reverse_api, urlencode(params)))
        
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_json(self, page, exactly_one=True):
        '''Returns location, (latitude, longitude) from json feed.'''

        places = page.get('results', [])
        if not len(places):
            self._check_status(page.get('status'))
            return self._check_status(page.get('status'))

        def parse_place(place):
            '''Get the location, lat, lng from a single json place.'''
            location = place.get('formatted_address')
            latitude = place['geometry']['location']['lat']
            longitude = place['geometry']['location']['lng']
            return Location(location, (latitude, longitude), place)

        if exactly_one:
            return parse_place(places[0])
        else:
            return [parse_place(place) for place in places]

    def _check_status(self, status):
        
        if status == "ok":
            return
        return status

