"""
:class:`Teleport` geocoder.
"""

from geopy.compat import urlencode
from geopy.exc import GeocoderServiceError
from geopy.geocoders.base import (
    Geocoder,
    DEFAULT_TIMEOUT,
    DEFAULT_FORMAT_STRING,
)
from geopy.location import Location
from geopy.util import logger
try:
    from urllib.parse import quote  # @UnresolvedImport @UnusedImport
except:
    from urllib import quote  # @Reimport


__all__ = ("Teleport", )


DEFAULT_FORWARD_EMBEDDINGS = (
    "city:search-results/city:item/{city:country,city:admin1_division}"
)
DEFAULT_REVERSE_EMBEDDINGS = (
    "location:nearest-cities/location:nearest-city" +
    "/{city:country,city:admin1_division}"
)


try:
    basestring
except:
    basestring = str  # @ReservedAssignment


class Teleport(Geocoder):
    """
    Teleport geocoder and reverse geocoder

    See API documentation at (https://developers.teleport.org/api/) for
    details.

    Example::

        from geopy.geocoders import Teleport
        from geopy.geocoders.teleport import DEFAULT_FORWARD_EMBEDDINGS

        teleport = Teleport(forward_embeddings=DEFAULT_FORWARD_EMBEDDINGS +
                            ",city:search-results/city:item/" +
                            "city:urban_area/ua:scores")
        locations = teleport.geocode("sfo", exactly_one=False)
        for location in locations:
            print (location.address,
                   location.point,
                   Teleport.get_embedded(location.raw,
                                         "city:item/city:urban_area/ua:scores",
                                         {})
                   .get('teleport_city_score'))

        location = teleport.reverse("37.774531,-122.418297")
        print (location.address,
               location.point,
               location.raw.get('distance_km'))

    """

    def __init__(self, format_string=DEFAULT_FORMAT_STRING, scheme='https',  # pylint: disable=R0913
                 timeout=DEFAULT_TIMEOUT, proxies=None, user_agent=None,
                 forward_embeddings=DEFAULT_FORWARD_EMBEDDINGS,
                 reverse_embeddings=DEFAULT_REVERSE_EMBEDDINGS):
        """
        :param string format_string: The format string where the input string
            to geocode is interpolated. For example, if you only need to
            geocode locations in Cleveland, Ohio, you could do
            format_string="%s, Cleveland OH"

        :param string scheme: The scheme/protocol to use to communicate with
            the API. Can be either 'https' (default) or 'http'.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

        :param string user_agent: The user agent string to send to the API in
            the User-Agent HTTP header.

        :param string forward_embeddings: The data to embed into responses for
            forward geocode requests (see the Teleport API documentation on
            how to compose the embed paths:
            https://developers.teleport.org/api/)

        :param string reverse_embeddings: The data to embed into responses for
            reverse geocode requests (see the Teleport API documentation on
            how to compose the embed paths:
            https://developers.teleport.org/api/)

        """
        super(Teleport, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent
        )
        self.forward_embeddings = forward_embeddings
        self.reverse_embeddings = reverse_embeddings
        self.api = "%s://api.teleport.org/api/cities/" % self.scheme
        self.api_reverse = (
            "%s://api.teleport.org/api/locations/%%s/" % self.scheme
        )

    def geocode(self, query, exactly_one=True, timeout=None):
        """
        Geocode a location query.

        :param string query: The city or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

            .. versionadded:: 0.97
        """
        params = {
            'search': self.format_string % (query,),
            'embed': self.forward_embeddings,
        }
        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one,
        )

    def reverse(self, query, exactly_one=True, timeout=None):
        """
        Given a point, find an address.

            .. versionadded:: 1.2.0

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
        coordinates = quote(self._coerce_point_to_string(query), safe=',')
        params = {
            'embed': self.reverse_embeddings,
        }
        url = self.api_reverse % (coordinates,)
        url = "?".join((url, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json_reverse(
            self._call_geocoder(url, timeout=timeout),
            exactly_one,
        )

    @staticmethod
    def get_embedded(parent, path, default=None):
        """
        Get an embedded sub-object of an object using the specified name or
        path.

        :param dict parent: The parent object to find embedded objects in

        :param string path: The embedded object path, e.g.
            "city:item/city:country"

        :param object default: The default value to return if the embedded
            object cannot be found
        """

        if isinstance(path, basestring):
            elements = path.split("/")
        else:
            elements = path
        name = elements[0]
        rest = elements[1:]
        embedded = parent.get('_embedded', {})
        relation = embedded.get(name, None)
        if relation is not None:
            if rest:
                return Teleport.get_embedded(relation, rest, default)
            else:
                return relation
        else:
            return default

    @staticmethod
    def _parse_city(city, raw_response, name=None):
        """
        Parse a city.
        """
        latlon = city.get('location', {}).get('latlon', {})
        latitude = latlon.get('latitude', None)
        longitude = latlon.get('longitude', None)

        if name is None:
            admin1 = Teleport.get_embedded(city, "city:admin1_division", {})
            country = Teleport.get_embedded(city, "city:country", {})

            parts = [city['name']]
            admin1_name = admin1.get('name')
            if admin1_name:
                parts.append(admin1_name)
            country_name = country.get('name')
            if country_name:
                parts.append(country_name)

            name = ", ".join(parts)

        return Location(name, (latitude, longitude), raw_response)

    def _parse_json(self, doc, exactly_one):
        """
        Parse JSON response body.
        """
        message = doc.get('message', None)
        if message is not None:
            raise GeocoderServiceError(message)

        search_results = Teleport.get_embedded(doc, 'city:search-results', [])
        if not len(search_results):
            return None

        def parse_result(search_result):
            """
            Parse a single result.
            """
            city = Teleport.get_embedded(search_result, 'city:item', {})
            name = search_result.get('matching_full_name')
            return self._parse_city(city, search_result, name=name)

        if exactly_one:
            return parse_result(search_results[0])
        else:
            return [parse_result(search_result)
                    for search_result in search_results]

    def _parse_json_reverse(self, doc, exactly_one):
        """
        Parse JSON response body.
        """
        message = doc.get('message', None)
        if message is not None:
            raise GeocoderServiceError(message)

        search_results = Teleport.get_embedded(doc,
                                               'location:nearest-cities', [])
        if not len(search_results):
            return None

        def parse_result(search_result):
            """
            Parse a single result.
            """
            city = Teleport.get_embedded(search_result,
                                         'location:nearest-city', {})
            return self._parse_city(city, search_result)

        if exactly_one:
            return parse_result(search_results[0])
        else:
            return [parse_result(search_result)
                    for search_result in search_results]
