import warnings

from geopy.compat import string_compare, urlencode
from geopy.exc import GeocoderQueryError
from geopy.geocoders.base import _DEFAULT_USER_AGENT, DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("Nominatim", )

_DEFAULT_NOMINATIM_DOMAIN = 'nominatim.openstreetmap.org'


class Nominatim(Geocoder):
    """Nominatim geocoder for OpenStreetMap data.

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

    geocode_path = '/search'
    reverse_path = '/reverse'

    def __init__(
            self,
            format_string=None,
            view_box=None,
            bounded=None,
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

        :type view_box: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.
        :param view_box: Coordinates to restrict search within.
            Example: ``[Point(22, 180), Point(-22, -180)]``.

            .. versionchanged:: 1.15.0
                Previously only a list of stringified coordinates was supported.

            .. versionchanged:: 1.17.0
                Previously view_box could be a list of 4 strings or numbers
                in the format of ``[longitude, latitude, longitude, latitude]``.
                This format is now deprecated in favor of a list/tuple
                of a pair of geopy Points and will be removed in geopy 2.0.

            .. deprecated:: 1.19.0
                This argument will be removed in geopy 2.0.
                Use `geocode`'s `viewbox` instead.

        :param bool bounded: Restrict the results to only items contained
            within the bounding view_box.

            .. versionadded:: 1.15.0

            .. deprecated:: 1.19.0
                This argument will be removed in geopy 2.0.
                Use `geocode`'s `bounded` instead.

        :type country_bias: str or list
        :param country_bias: Limit search results to a specific country.
            This param sets a default value for the `geocode`'s ``country_codes``.

            .. deprecated:: 1.19.0
                This argument will be removed in geopy 2.0.
                Use `geocode`'s `country_codes` instead.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str domain: Domain where the target Nominatim service
            is hosted.

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

        if country_bias is not None:
            warnings.warn(
                '`country_bias` argument of the %(cls)s.__init__ '
                'is deprecated and will be removed in geopy 2.0. Use '
                '%(cls)s.geocode(country_codes=%(value)r) instead.'
                % dict(cls=type(self).__name__, value=country_bias),
                DeprecationWarning,
                stacklevel=2
            )
        self.country_bias = country_bias

        if view_box is not None:
            warnings.warn(
                '`view_box` argument of the %(cls)s.__init__ '
                'is deprecated and will be removed in geopy 2.0. Use '
                '%(cls)s.geocode(viewbox=%(value)r) instead.'
                % dict(cls=type(self).__name__, value=view_box),
                DeprecationWarning,
                stacklevel=2
            )
        self.view_box = view_box

        if bounded is not None:
            warnings.warn(
                '`bounded` argument of the %(cls)s.__init__ '
                'is deprecated and will be removed in geopy 2.0. Use '
                '%(cls)s.geocode(bounded=%(value)r) instead.'
                % dict(cls=type(self).__name__, value=bounded),
                DeprecationWarning,
                stacklevel=2
            )
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
                DeprecationWarning,
                stacklevel=2
            )

        self.api = "%s://%s%s" % (self.scheme, self.domain, self.geocode_path)
        self.reverse_api = "%s://%s%s" % (self.scheme, self.domain, self.reverse_path)

    def _construct_url(self, base_api, params):
        """
        Construct geocoding request url.
        The method can be overridden in Nominatim-based geocoders in order
        to extend URL parameters.

        :param str base_api: Geocoding function base address - self.api
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
            geometry=None,
            extratags=False,
            country_codes=None,
            viewbox=None,
            bounded=None,  # TODO: change default value to `False` in geopy 2.0
            featuretype=None,
            namedetails=False,
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

        :param bool extratags: Include additional information in the result if available,
            e.g. wikipedia link, opening hours.

            .. versionadded:: 1.17.0

        :param country_codes: Limit search results
            to a specific country (or a list of countries).
            A country_code should be the ISO 3166-1alpha2 code,
            e.g. ``gb`` for the United Kingdom, ``de`` for Germany, etc.

            .. versionadded:: 1.19.0

        :type country_codes: str or list

        :type viewbox: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.

        :param viewbox: Coordinates to restrict search within.
            Example: ``[Point(22, 180), Point(-22, -180)]``.

            .. versionadded:: 1.19.0

        :param bool bounded: Restrict the results to only items contained
            within the bounding view_box. Defaults to `False`.

            .. versionadded:: 1.19.0

        :param str featuretype: If present, restrict results to certain type of features.
            Allowed values: `country`, `state`, `city`, `settlement`.

            .. versionadded:: 1.21.0

        :param bool namedetails: If you want in *Location.raw* to include
            namedetails, set it to True. This will be a list of alternative names,
            including language variants, etc.

            .. versionadded:: 1.21.0

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
        elif limit is not None:
            limit = int(limit)
            if limit < 1:
                raise ValueError("Limit cannot be less than 1")
            params['limit'] = limit

        if viewbox is None:
            viewbox = self.view_box
        if viewbox:
            if len(viewbox) == 4:
                warnings.warn(
                    '%s `viewbox` format of '
                    '`[longitude, latitude, longitude, latitude]` is now '
                    'deprecated and will not be supported in geopy 2.0. '
                    'Use `[Point(latitude, longitude), Point(latitude, longitude)]` '
                    'instead.' % type(self).__name__,
                    DeprecationWarning,
                    stacklevel=2
                )
                lon1, lat1, lon2, lat2 = viewbox
                viewbox = [[lat1, lon1], [lat2, lon2]]
            params['viewbox'] = self._format_bounding_box(
                viewbox, "%(lon1)s,%(lat1)s,%(lon2)s,%(lat2)s")

        if bounded is None:
            bounded = self.bounded
        if bounded:
            params['bounded'] = 1

        if country_codes is None:
            country_codes = self.country_bias
        if not country_codes:
            country_codes = []
        if isinstance(country_codes, string_compare):
            country_codes = [country_codes]
        if country_codes:
            params['countrycodes'] = ",".join(country_codes)

        if addressdetails:
            params['addressdetails'] = 1

        if namedetails:
            params['namedetails'] = 1

        if language:
            params['accept-language'] = language

        if extratags:
            params['extratags'] = True

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

        if featuretype:
            params['featuretype'] = featuretype

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
            lat, lon = self._coerce_point_to_string(query).split(',')
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
        if latitude is not None and longitude is not None:
            latitude = float(latitude)
            longitude = float(longitude)
        return Location(placename, (latitude, longitude), place)

    def _parse_json(self, places, exactly_one):
        if not places:
            return None
        if not isinstance(places, list):
            places = [places]
        if exactly_one:
            return self.parse_code(places[0])
        else:
            return [self.parse_code(place) for place in places]
