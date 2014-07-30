"""
:class:`.MapQuest` geocoder.
"""

from geopy.compat import urlencode
from geopy.geocoders.base import (
    Geocoder,
    DEFAULT_FORMAT_STRING,
    DEFAULT_TIMEOUT,
    DEFAULT_SCHEME
)
from geopy.location import Location
from geopy.util import logger, join_filter
from geopy import exc


__all__ = ("MapQuest", )


class MapQuest(Geocoder): # pylint: disable=W0223
    """
    MapQuest geocoder, documentation at:
        http://www.mapquestapi.com/geocoding/
    """

    def __init__(
            self,
            api_key,
            format_string=DEFAULT_FORMAT_STRING,
            scheme=DEFAULT_SCHEME,
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
        ):  # pylint: disable=R0913
        """
        Initialize a MapQuest geocoder with address information and
        MapQuest API key.

        :param string api_key: Key provided by MapQuest.

        :param string format_string: String containing '%s' where the
            string to geocode should be interpolated before querying the
            geocoder. For example: '%s, Mountain View, CA'. The default
            is just '%s'.

        :param string scheme: Use 'https' or 'http' as the API URL's scheme.
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
        """
        super(MapQuest, self).__init__(format_string, scheme, timeout, proxies)
        self.api_key = api_key
        self.api = (
            "%s://www.mapquestapi.com/geocoding/v1/address" % self.scheme
        )

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
            .. versionadded:: 0.97
        """
        params = {
            'location' : self.format_string % query
        }
        if exactly_one:
            params['maxResults'] = 1
        # don't urlencode MapQuest API keys
        url = "?".join((
            self.api,
            "&".join(("=".join(('key', self.api_key)), urlencode(params)))
        ))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one
        )

    def _parse_json(self, resources, exactly_one=True):
        """
        Parse display name, latitude, and longitude from an JSON response.
        """
        if resources.get('info').get('statuscode') == 403:
            raise exc.GeocoderAuthenticationFailure()

        resources = resources.get('results')[0].get('locations', [])
        if not len(resources):
            return None

        def parse_resource(resource):
            """
            Parse each record.
            """
            city = resource['adminArea5']
            county = resource['adminArea4']
            state = resource['adminArea3']
            country = resource['adminArea1']
            latLng = resource['latLng']
            latitude, longitude = latLng.get('lat'), latLng.get('lng')

            location = join_filter(", ", [city, county, state, country])
            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)

            return Location(location, (latitude, longitude), resource)

        if exactly_one:
            return parse_resource(resources[0])
        else:
            return [parse_resource(resource) for resource in resources]
