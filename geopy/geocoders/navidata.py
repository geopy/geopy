"""
:class:`.NaviData` is the NaviData.pl geocoder.
"""

from geopy.compat import urlencode, string_compare
from geopy.location import Location
from geopy.point import Point
from geopy.util import logger
from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT, DEFAULT_SCHEME

from geopy.exc import (
    GeocoderQueryError,
    GeocoderQuotaExceeded,
)


__all__ = ("NaviData", )



class NaviData(Geocoder):
    """
    Geocoder using the NaviData  API.
    """

    def __init__(
            self,
            api_key=None,
            domain='api.navidata.pl',
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
    ):
        """
        Initialize a customized NaviData geocoder.

        :param string api_key: The commercial API key for service. None required if you
            use this API for non-commercial puproses

        :param string domain: Currently it is 'api.navidata.pl', can
            be changed for testing purposes.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

        """
        super(NaviData, self).__init__(
            scheme="http", timeout=timeout, proxies=proxies
        )

        self.api_key = api_key
        self.domain = domain.strip('/')
        #self.scheme = scheme
        self.geocode_api = 'http://%s/geocode' % (self.domain)
        self.reverse_geocode_api = 'http://%s/revGeo' % (self.domain)

    def geocode(
            self,
            query,
            exactly_one=True,
            timeout=None,
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

        """
        params = {
            'q': self.format_string % query,
        }


        if self.api_key is not None:
            params["api_key"] = self.api_key

        url = "?".join((self.geocode_api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    def reverse(
            self,
            query,
            exactly_one=False,
            timeout=None,
    ):

        """
        Given a point, find an address.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param boolean exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        """
        params = {
            'lat': self._coerce_point_to_string(query, 'lat'),
            'lon': self._coerce_point_to_string(query, 'lon')
        }


        if self.api_key is not None:
            params["api_key"] = self.api_key

        url = "?".join((self.reverse_geocode_api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    def _parse_json(self, page, exactly_one=True):
        '''Returns location, (latitude, longitude) from json feed.'''

        places = page

        if not len(places):
            self._check_status(page.get('status'))
            return None

        def parse_place(place):
            '''Get the location, lat, lon from a single json result.'''
            location = place.get('description')
            latitude = place.get('lat')
            longitude = place.get('lon')
            return Location(location, (latitude, longitude), place)

        if exactly_one:
            return parse_place(places[0])
        else:
            return [parse_place(place) for place in places]



    def _coerce_point_to_string(self, point, type):
        """
        Do the right thing on "point" input.
        """

        if isinstance(point, Point):

            if type == "lat":
                return str(point.latitude)
            else:
                return str(point.longitude)

        elif isinstance(point, (list, tuple)):

            if type == "lat":
                return str(point[0])
            else:
                return str(point[1])


        elif isinstance(point, string_compare):

            if type == "lat":
                return point.split(',')[0]
            else:
                return point.split(',')[1]

        else:
            raise ValueError("Invalid point")

    @staticmethod
    def _check_status(status):
        """
        Validates error statuses.
        """
        status_code = status['code']
        if status_code == 429:
            # Rate limit exceeded
            raise GeocoderQuotaExceeded(
                'The given key has gone over the requests limit in the 24'
                ' hour period or has submitted too many requests in too'
                ' short a period of time.'
            )
        if status_code == 200:
            # When there are no results, just return.
            return

        if status_code == 403:
            raise GeocoderQueryError(
                'Your request was denied.'
            )
        else:
            raise GeocoderQueryError('Unknown error.')
