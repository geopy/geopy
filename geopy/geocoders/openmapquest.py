"""
:class:`.OpenMapQuest` geocoder.
"""

from geopy.compat import urlencode
from geopy.exc import ConfigurationError
from geopy.geocoders.base import (
    Geocoder,
    DEFAULT_FORMAT_STRING,
    DEFAULT_TIMEOUT,
    DEFAULT_SCHEME
)
from geopy.location import Location
from geopy.util import logger


__all__ = ("OpenMapQuest", )


class OpenMapQuest(Geocoder): # pylint: disable=W0223
    """
    Geocoder using MapQuest Open Platform Web Services. Documentation at:
        https://developer.mapquest.com/documentation/open/
    """

    def __init__(
            self,
            api_key=None,
            format_string=DEFAULT_FORMAT_STRING,
            scheme=DEFAULT_SCHEME,
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
            user_agent=None,
        ):  # pylint: disable=R0913
        """
        Initialize an Open MapQuest geocoder with location-specific
        address information.

        :param str api_key: API key provided by MapQuest.

            .. versionchanged:: 1.12.0
               OpenMapQuest now requires an API key. Using an empty key will
               result in a :class:`geopy.exc.ConfigurationError`.

        :param str format_string: String containing '%s' where
            the string to geocode should be interpolated before querying
            the geocoder. For example: '%s, Mountain View, CA'. The default
            is just '%s'.

        :param str scheme: Use 'https' or 'http' as the API URL's scheme.
            Default is https. Note that SSL connections' certificates are not
            verified.

            .. versionadded:: 0.97

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

            .. versionadded:: 0.97

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

            .. versionadded:: 0.96

        :param str user_agent: Use a custom User-Agent header.

            .. versionadded:: 1.12.0
        """
        super(OpenMapQuest, self).__init__(
            format_string, scheme, timeout, proxies, user_agent=user_agent
        )
        if not api_key:
            raise ConfigurationError('OpenMapQuest requires an API key')
        self.api_key = api_key
        self.api = "%s://open.mapquestapi.com/nominatim/v1/search" \
                    "?format=json" % self.scheme

    def geocode(self, query, exactly_one=True, timeout=None): # pylint: disable=W0221
        """
        Geocode a location query.

        :param str query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

            .. versionadded:: 0.97
        """
        params = {
            'key': self.api_key,
            'q': self.format_string % query
        }
        if exactly_one:
            params['maxResults'] = 1
        url = "&".join((self.api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one
        )

    @classmethod
    def _parse_json(cls, resources, exactly_one=True):
        """
        Parse display name, latitude, and longitude from an JSON response.
        """
        if not len(resources): # pragma: no cover
            return None
        if exactly_one:
            return cls.parse_resource(resources[0])
        else:
            return [cls.parse_resource(resource) for resource in resources]

    @classmethod
    def parse_resource(cls, resource):
        """
        Return location and coordinates tuple from dict.
        """
        location = resource['display_name']

        latitude = resource['lat'] or None
        longitude = resource['lon'] or None
        if latitude and longitude:
            latitude = float(latitude)
            longitude = float(longitude)

        return Location(location, (latitude, longitude), resource)
