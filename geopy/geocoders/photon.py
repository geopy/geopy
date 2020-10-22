import collections.abc
from functools import partial
from urllib.parse import urlencode

from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("Photon", )


class Photon(Geocoder):
    """Geocoder using Photon geocoding service (data based on OpenStreetMap
    and service provided by Komoot on https://photon.komoot.de).

    Documentation at:
        https://github.com/komoot/photon

    Photon/Komoot geocoder aims to let you `search as you type with
    OpenStreetMap`. No API Key is needed by this platform.
    """

    geocode_path = '/api'
    reverse_path = '/reverse'

    def __init__(
            self,
            *,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            domain='photon.komoot.de',
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str domain: Should be the localized Photon domain to
            connect to. The default is ``'photon.komoot.de'``, but you
            can change it to a domain of your own.

        :param str user_agent:
            See :attr:`geopy.geocoders.options.default_user_agent`.

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.

        :param callable adapter_factory:
            See :attr:`geopy.geocoders.options.default_adapter_factory`.

            .. versionadded:: 2.0
        """
        super().__init__(
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )
        self.domain = domain.strip('/')
        self.api = "%s://%s%s" % (self.scheme, self.domain, self.geocode_path)
        self.reverse_api = "%s://%s%s" % (self.scheme, self.domain, self.reverse_path)

    def geocode(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            location_bias=None,
            language=False,
            limit=None,
            osm_tag=None
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param location_bias: The coordinates to used as location bias.

        :param str language: Preferred language in which to return results.

        :param int limit: Limit the number of returned results, defaults to no
            limit.

        :param osm_tag: The expression to filter (include/exclude) by key and/
            or value, str as ``'key:value'`` or list/set of str if multiple
            filters are required as ``['key:!val', '!key', ':!value']``.
        :type osm_tag: str or list or set

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """
        params = {
            'q': query
        }
        if limit:
            params['limit'] = int(limit)
        if exactly_one:
            params['limit'] = 1
        if language:
            params['lang'] = language
        if location_bias:
            try:
                lat, lon = self._coerce_point_to_string(location_bias).split(',')
                params['lon'] = lon
                params['lat'] = lat
            except ValueError:
                raise ValueError(("Location bias must be a"
                                  " coordinate pair or Point"))
        if osm_tag:
            if isinstance(osm_tag, str):
                params['osm_tag'] = [osm_tag]
            else:
                if not isinstance(osm_tag, collections.abc.Iterable):
                    raise ValueError(
                        "osm_tag must be a string or "
                        "an iterable of strings"
                    )
                params['osm_tag'] = list(osm_tag)
        url = "?".join((self.api, urlencode(params, doseq=True)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            language=False,
            limit=None
    ):
        """
        Return an address by location point.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param str language: Preferred language in which to return results.

        :param int limit: Limit the number of returned results, defaults to no
            limit.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        try:
            lat, lon = self._coerce_point_to_string(query).split(',')
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
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_json(self, resources, exactly_one=True):
        """
        Parse display name, latitude, and longitude from a JSON response.
        """
        if not len(resources['features']):  # pragma: no cover
            return None
        if exactly_one:
            return self._parse_resource(resources['features'][0])
        else:
            return [self._parse_resource(resource) for resource
                    in resources['features']]

    def _parse_resource(self, resource):
        # Return location and coordinates tuple from dict.
        name_elements = ['name', 'housenumber', 'street',
                         'postcode', 'street', 'city',
                         'state', 'country']
        name = [resource['properties'].get(k) for k
                in name_elements if resource['properties'].get(k)]
        location = ', '.join(name)

        latitude = resource['geometry']['coordinates'][1]
        longitude = resource['geometry']['coordinates'][0]
        if latitude and longitude:
            latitude = float(latitude)
            longitude = float(longitude)

        return Location(location, (latitude, longitude), resource)
