"""
:class:`Yandex` geocoder.
"""

from geopy.compat import urlencode

from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT
from geopy.location import Location
from geopy.exc import (
    GeocoderServiceError,
    GeocoderParseError
)
from geopy.util import logger


__all__ = ("Yandex", )


class Yandex(Geocoder): # pylint: disable=W0223
    """
    Yandex geocoder, documentation at:
        http://api.yandex.com/maps/doc/geocoder/desc/concepts/input_params.xml
    """

    def __init__(
            self,
            timeout=DEFAULT_TIMEOUT,
            proxies=None
        ):
        """
        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.
        """
        super(Yandex, self).__init__(
            scheme='http', timeout=timeout, proxies=proxies
        )
        self.api = 'http://geocode-maps.yandex.ru/1.x/'

    def geocode(self, query, exactly_one=True, timeout=None): # pylint: disable=W0221
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.
        """
        params = {
            'geocode': query,
            'format': 'json'
        }
        if exactly_one is True:
            params['results'] = 1
        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one,
        )

    def reverse(
            self,
            query,
            exactly_one=False,
            timeout=None,
        ):
        """
        Given a point, find an address.

        :param string query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param boolean exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

        """
        try:
            lat, lng = [
              x.strip() for x in
              self._coerce_point_to_string(query).split(',')
            ]
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")
        params = {
            'geocode': '{0},{1}'.format(lng, lat),
            'format': 'json'
        }
        url = "?".join((self.api, urlencode(params)))
        print url
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one
        )

    def _parse_json(self, doc, exactly_one):
        """
        Parse JSON response body.
        """
        if doc.get('error'):
            raise GeocoderServiceError(doc['error']['message'])

        try:
            places = doc['response']['GeoObjectCollection']['featureMember']
        except KeyError:
            raise GeocoderParseError('Failed to parse server response')

        def parse_code(place):
            """
            Parse each record.
            """
            try:
                place = place['GeoObject']
            except KeyError:
                raise GeocoderParseError('Failed to parse server response')

            longitude, latitude = map(float, place['Point']['pos'].split(' '))
            
            location = place.get('description')

            return Location(location, (latitude, longitude), place)

        if exactly_one:
            return parse_code(places[0])
        else:
            return [parse_code(place) for place in places]
