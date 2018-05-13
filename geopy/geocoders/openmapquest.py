"""
:class:`.OpenMapQuest` geocoder.
"""

from geopy.compat import urlencode
from geopy.exc import ConfigurationError
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("OpenMapQuest", )


class OpenMapQuest(Geocoder): # pylint: disable=W0223
    """Geocoder using MapQuest Open Platform Web Services.

    Documentation at:
        https://developer.mapquest.com/documentation/open/
    """

    def __init__(
            self,
            api_key=None,
            format_string=None,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """

        :param str api_key: API key provided by MapQuest, required.

            .. versionchanged:: 1.12.0
               OpenMapQuest now requires an API key. Using an empty key will
               result in a :class:`geopy.exc.ConfigurationError`.

        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str user_agent:
            See :attr:`geopy.geocoders.options.default_user_agent`.

            .. versionadded:: 1.12.0

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.

            .. versionadded:: 1.14.0
        """
        super(OpenMapQuest, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )
        if not api_key:
            raise ConfigurationError('OpenMapQuest requires an API key')
        self.api_key = api_key
        self.api = "%s://open.mapquestapi.com/nominatim/v1/search" \
                    "?format=json" % self.scheme

    def geocode(self, query, exactly_one=True, timeout=DEFAULT_SENTINEL):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
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
        if not len(resources):
            return None
        if exactly_one:
            return cls.parse_resource(resources[0])
        else:
            return [cls.parse_resource(resource) for resource in resources]

    @classmethod
    def parse_resource(cls, resource):
        # TODO make this a private API
        # Return location and coordinates tuple from dict.
        location = resource['display_name']

        latitude = resource['lat'] or None
        longitude = resource['lon'] or None
        if latitude and longitude:
            latitude = float(latitude)
            longitude = float(longitude)

        return Location(location, (latitude, longitude), resource)
