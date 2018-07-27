import warnings
from itertools import chain

from geopy.compat import urlencode
from geopy.exc import GeocoderQueryError
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder, _DEFAULT_USER_AGENT
from geopy.location import Location
from geopy.util import logger
from geopy.point import Point

__all__ = ("Nominatim", )

_DEFAULT_NOMINATIM_DOMAIN = 'nominatim.openstreetmap.org'


class Nominatim(Geocoder):
    """Nominatim geocoder for OpenStreetMap servers.

    Documentation at:
        https://wiki.openstreetmap.org/wiki/Nominatim

    .. attention::
       Using Nominatim with the default `user_agent` is strongly discouraged,
       as it violates Nominatim's Usage Policy
       https://operations.osmfoundation.org/policies/nominatim/
       and may possibly cause 403 and 429 HTTP errors. Please make sure
       to specify a custom `user_agent` with
       ``Nominatim(user_agent="my-application")`` or by
       overriding the default `user_agent`:
       ``geopy.geocoders.options.default_user_agent = "my-application"``.
       In geopy 2.0 an exception will be thrown when a custom
       `user_agent` is not specified.

    .. versionchanged:: 1.16.0
       A warning is now issued when a default `user_agent` is used
       which restates the `Attention` block above.
    """

    structured_query_params = {
        'street',
        'city',
        'county',
        'state',
        'country',
        'postalcode',
    }

    def __init__(
            self,
            format_string=None,
            view_box=None,
            bounded=False,
            country_bias=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            domain=_DEFAULT_NOMINATIM_DOMAIN,
            scheme=None,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            # Make sure to synchronize the changes of this signature in the
            # inheriting classes (e.g. PickPoint).
    ):
        """
        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

        :param tuple view_box: Coordinates to restrict search within.
            Accepts instances of the :class:`geopy.point.Point`
            ``[Point(22, 180), Point(-22, -180)]``,
            or iterables of numeric and string types ``[180, 22, -180, -22]``,
            ``["180", "22", "-180", "-22"]``

            .. versionchanged:: 1.15.0
               Previously only a list of stringified coordinates was supported.

        :param str country_bias: Bias results to this country.

        :param bool bounded: Restrict the results to only items contained
            within the bounding view_box.

            .. versionadded:: 1.15.0

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str domain: Should be the localized Openstreetmap domain to
            connect to. The default is ``'nominatim.openstreetmap.org'``,
            but you can change it to a domain of your own.

            .. versionadded:: 1.8.2

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`.

            .. versionadded:: 1.8.2

        :param str user_agent:
            See :attr:`geopy.geocoders.options.default_user_agent`.

            .. versionadded:: 1.12.0

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.

            .. versionadded:: 1.14.0

        """
        super(Nominatim, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )
        self.country_bias = country_bias
        self.view_box = view_box
        self.bounded = bounded
        self.domain = domain.strip('/')

        if (self.domain == _DEFAULT_NOMINATIM_DOMAIN
                and self.headers['User-Agent'] == _DEFAULT_USER_AGENT):
            warnings.warn(
                'Using Nominatim with the default "%s" `user_agent` is '
                'strongly discouraged, as it violates Nominatim\'s ToS '
                'https://operations.osmfoundation.org/policies/nominatim/ '
                'and may possibly cause 403 and 429 HTTP errors. '
                'Please specify a custom `user_agent` with '
                '`Nominatim(user_agent="my-application")` or by '
                'overriding the default `user_agent`: '
                '`geopy.geocoders.options.default_user_agent = "my-application"`. '
                'In geopy 2.0 this will become an exception.'
                % _DEFAULT_USER_AGENT,
                UserWarning
            )

        self.api = "%s://%s/search" % (self.scheme, self.domain)
        self.reverse_api = "%s://%s/reverse" % (self.scheme, self.domain)

    def _construct_url(self, base_api, params):
        """
        Construct geocoding request url.
        The method can be overriden in Nominatim-based geocoders in order
        to extend URL parameters.

        :param string base_api: Geocoding function base address - self.api
            or self.reverse_api.

        :param dict params: Geocoding params.

        :return: string URL.
        """
        return "?".join((base_api, urlencode(params)))

    def geocode(
            self,
            query,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            limit=None,
            addressdetails=False,
            language=False,
            geometry=None
    ):
        """
        Return a location point by address.

        :param query: The address, query or a structured query
            you wish to geocode.

            .. versionchanged:: 1.0.0
                For a structured query, provide a dictionary whose keys
                are one of: `street`, `city`, `county`, `state`, `country`, or
                `postalcode`. For more information, see Nominatim's
                documentation for `structured requests`:

                    https://wiki.openstreetmap.org/wiki/Nominatim

        :type query: dict or str

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param int limit: Maximum amount of results to return from Nominatim.
            Unless exactly_one is set to False, limit will always be 1.

            .. versionadded:: 1.13.0

        :param bool addressdetails: If you want in *Location.raw* to include
            addressdetails such as city_district, etc set it to True

        :param str language: Preferred language in which to return results.
            Either uses standard
            `RFC2616 <http://www.ietf.org/rfc/rfc2616.txt>`_
            accept-language string or a simple comma-separated
            list of language codes.

            .. versionadded:: 1.0.0

        :param str geometry: If present, specifies whether the geocoding
            service should return the result's geometry in `wkt`, `svg`,
            `kml`, or `geojson` formats. This is available via the
            `raw` attribute on the returned :class:`geopy.location.Location`
            object.

            .. versionadded:: 1.3.0

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """

        if isinstance(query, dict):
            params = {
                key: val
                for key, val
                in query.items()
                if key in self.structured_query_params
            }
        else:
            params = {'q': self.format_string % query}

        params.update({
            'format': 'json'
        })

        if exactly_one:
            params['limit'] = 1
        elif limit:
            limit = int(limit)
            if limit < 1:
                raise ValueError("Limit cannot be less than 1")
            params['limit'] = limit

        # `viewbox` apparently replaces `view_box`
        if self.view_box:
            if all(isinstance(point, Point) for point in self.view_box):
                p1, p2 = self.view_box
                params['viewbox'] = ','.join(str(p) for p in chain(p1[1::-1], p2[1::-1]))
            else:
                params['viewbox'] = ','.join(str(coord) for coord in self.view_box)

        if self.bounded:
            params['bounded'] = 1

        if self.country_bias:
            params['countrycodes'] = self.country_bias

        if addressdetails:
            params['addressdetails'] = 1

        if language:
            params['accept-language'] = language

        if geometry is not None:
            geometry = geometry.lower()
            if geometry == 'wkt':
                params['polygon_text'] = 1
            elif geometry == 'svg':
                params['polygon_svg'] = 1
            elif geometry == 'kml':
                params['polygon_kml'] = 1
            elif geometry == 'geojson':
                params['polygon_geojson'] = 1
            else:
                raise GeocoderQueryError(
                    "Invalid geometry format. Must be one of: "
                    "wkt, svg, kml, geojson."
                )

        url = self._construct_url(self.api, params)
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)

        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    def reverse(
            self,
            query,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            language=False,
            addressdetails=True
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
            Either uses standard
            `RFC2616 <http://www.ietf.org/rfc/rfc2616.txt>`_
            accept-language string or a simple comma-separated
            list of language codes.

            .. versionadded:: 1.0.0

        :param bool addressdetails: Whether or not to include address details,
            such as city, county, state, etc. in *Location.raw*

            .. versionadded:: 1.14.0

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """
        try:
            lat, lon = [
                x.strip() for x in
                self._coerce_point_to_string(query).split(',')
            ]  # doh
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
        }
        if language:
            params['accept-language'] = language

        params['addressdetails'] = 1 if addressdetails else 0

        url = self._construct_url(self.reverse_api, params)
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)

        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    @staticmethod
    def parse_code(place):
        # TODO make this a private API
        # Parse each resource.
        latitude = place.get('lat', None)
        longitude = place.get('lon', None)
        placename = place.get('display_name', None)
        if latitude and longitude:
            latitude = float(latitude)
            longitude = float(longitude)
        return Location(placename, (latitude, longitude), place)

    def _parse_json(self, places, exactly_one):
        if places is None:
            return None
        if not isinstance(places, list):
            places = [places]
        if not len(places):
            return None
        if exactly_one:
            return self.parse_code(places[0])
        else:
            return [self.parse_code(place) for place in places]
