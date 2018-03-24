"""
:class:`.Photon` geocoder.
"""

from geopy.compat import urlencode, string_compare
from geopy.geocoders.base import (
    Geocoder,
    DEFAULT_FORMAT_STRING,
    DEFAULT_TIMEOUT,
    DEFAULT_SCHEME
)
from geopy.location import Location
from geopy.util import logger


__all__ = ("Photon", )


class Photon(Geocoder):  # pylint: disable=W0223
    """
    Geocoder using Photon geocoding service (data based on OpenStreetMap and
    service provided by Komoot on https://photon.komoot.de).
    Documentation at https://github.com/komoot/photon
    """

    def __init__(
            self,
            format_string=DEFAULT_FORMAT_STRING,
            scheme=DEFAULT_SCHEME,
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
            domain='photon.komoot.de',
            user_agent=None,
    ):   # pylint: disable=R0913
        """
        Initialize a Photon/Komoot geocoder which aims to let you "search as
        you type with OpenStreetMap". No API Key is needed by this platform.

        :param str format_string: String containing '%s' where
            the string to geocode should be interpolated before querying
            the geocoder. For example: '%s, Mountain View, CA'. The default
            is just '%s'.

        :param str scheme: Use 'https' or 'http' as the API URL's scheme.
            Default is https. Note that SSL connections' certificates are not
            verified.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

        :param str domain: Should be the localized Photon domain to
            connect to. The default is 'photon.komoot.de', but you
            can change it to a domain of your own.

        :param str user_agent: Use a custom User-Agent header.

            .. versionadded:: 1.12.0
        """
        super(Photon, self).__init__(
            format_string, scheme, timeout, proxies, user_agent=user_agent
        )
        self.domain = domain.strip('/')
        self.api = "%s://%s/api" % (self.scheme, self.domain)
        self.reverse_api = "%s://%s/reverse" % (self.scheme, self.domain)

    def geocode(
            self,
            query,
            exactly_one=True,
            timeout=None,
            location_bias=None,
            language=False,
            limit=None,
            osm_tag=None
        ):  # pylint: disable=W0221
        """
        Geocode a location query.

        :param str query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param location_bias: The coordinates to used as location bias.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param str language: Preferred language in which to return results.

        :param int limit: Limit the number of returned results, defaults to no
            limit.

            .. versionadded:: 1.12.0

        :param osm_tag: The expression to filter (include/exclude) by key and/
            or value, str as 'key:value' or list/set of str if multiple filters
            are required as ['key:!val', '!key', ':!value'].
        :type osm_tag: str or list or set

        """
        params = {
            'q': self.format_string % query
        }
        if limit:
            params['limit'] = int(limit)
        if exactly_one:
            params['limit'] = 1
        if language:
            params['lang'] = language
        if location_bias:
            try:
                lat, lon = [x.strip() for x
                            in self._coerce_point_to_string(location_bias)
                            .split(',')]
                params['lon'] = lon
                params['lat'] = lat
            except ValueError:
                raise ValueError(("Location bias must be a"
                                  " coordinate pair or Point"))
        if osm_tag:
            if isinstance(osm_tag, string_compare):
                params['osm_tag'] = [osm_tag]
            else:
                if not isinstance(osm_tag, (list, set)):
                    raise ValueError(
                        "osm_tag must be a string expression or "
                        "a set/list of string expressions"
                    )
                params['osm_tag'] = osm_tag
        url = "?".join((self.api, urlencode(params, doseq=True)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one
        )

    def reverse(
            self,
            query,
            exactly_one=True,
            timeout=None,
            language=False,
            limit=None,
        ):  # pylint: disable=W0221
        """
        Returns a reverse geocoded location.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param str language: Preferred language in which to return results.

        :param int limit: Limit the number of returned results, defaults to no
            limit.

            .. versionadded:: 1.12.0

        """
        try:
            lat, lon = [x.strip() for x in
                        self._coerce_point_to_string(query).split(',')]
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")
        params = {
            'lat': lat,
            'lon': lon,
        }
        if limit:
            params['limit'] = int(limit)
        if exactly_one:
            params['limit'] = 1
        if language:
            params['lang'] = language
        url = "?".join((self.reverse_api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    @classmethod
    def _parse_json(cls, resources, exactly_one=True):
        """
        Parse display name, latitude, and longitude from a JSON response.
        """
        if not len(resources['features']):  # pragma: no cover
            return None
        if exactly_one:
            return cls.parse_resource(resources['features'][0])
        else:
            return [cls.parse_resource(resource) for resource
                    in resources['features']]

    @classmethod
    def parse_resource(cls, resource):
        """
        Return location and coordinates tuple from dict.
        """
        name_elements = ['name', 'housenumber', 'street',
                         'postcode', 'street', 'city',
                         'state', 'country']
        name = [resource['properties'].get(k) for k
                in name_elements if resource['properties'].get(k)]
        location = ', '.join(name)

        latitude = resource['geometry']['coordinates'][1] or None
        longitude = resource['geometry']['coordinates'][0] or None
        if latitude and longitude:
            latitude = float(latitude)
            longitude = float(longitude)

        return Location(location, (latitude, longitude), resource)
