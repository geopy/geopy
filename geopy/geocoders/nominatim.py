import collections.abc
from functools import partial
from urllib.parse import urlencode

from geopy.exc import ConfigurationError, GeocoderQueryError
from geopy.geocoders.base import _DEFAULT_USER_AGENT, DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("Nominatim", )

_DEFAULT_NOMINATIM_DOMAIN = 'nominatim.openstreetmap.org'
_REJECTED_USER_AGENTS = (
    # Various sample user-agent strings mentioned in docs:
    "my-application",
    "my_app/1",
    "my_user_agent/1.0",
    "specify_your_app_name_here",
    _DEFAULT_USER_AGENT,
)


class Nominatim(Geocoder):
    """Nominatim geocoder for OpenStreetMap data.

    Documentation at:
        https://nominatim.org/release-docs/develop/api/Overview/

    .. attention::
       Using Nominatim with the default `user_agent` is strongly discouraged,
       as it violates Nominatim's Usage Policy
       https://operations.osmfoundation.org/policies/nominatim/
       and may possibly cause 403 and 429 HTTP errors. Please make sure
       to specify a custom `user_agent` with
       ``Nominatim(user_agent="my-application")`` or by
       overriding the default `user_agent`:
       ``geopy.geocoders.options.default_user_agent = "my-application"``.
       An exception will be thrown if a custom `user_agent` is not specified.
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
            *,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            domain=_DEFAULT_NOMINATIM_DOMAIN,
            scheme=None,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
            # Make sure to synchronize the changes of this signature in the
            # inheriting classes (e.g. PickPoint).
    ):
        """

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str domain: Domain where the target Nominatim service
            is hosted.

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`.

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

        if (self.domain == _DEFAULT_NOMINATIM_DOMAIN
                and self.headers['User-Agent'] in _REJECTED_USER_AGENTS):
            raise ConfigurationError(
                'Using Nominatim with default or sample `user_agent` "%s" is '
                'strongly discouraged, as it violates Nominatim\'s ToS '
                'https://operations.osmfoundation.org/policies/nominatim/ '
                'and may possibly cause 403 and 429 HTTP errors. '
                'Please specify a custom `user_agent` with '
                '`Nominatim(user_agent="my-application")` or by '
                'overriding the default `user_agent`: '
                '`geopy.geocoders.options.default_user_agent = "my-application"`.'
                % self.headers['User-Agent']
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
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            limit=None,
            addressdetails=False,
            language=False,
            geometry=None,
            extratags=False,
            country_codes=None,
            viewbox=None,
            bounded=False,
            featuretype=None,
            namedetails=False
    ):
        """
        Return a location point by address.

        :param query: The address, query or a structured query
            you wish to geocode.

            For a structured query, provide a dictionary whose keys
            are one of: `street`, `city`, `county`, `state`, `country`, or
            `postalcode`. For more information, see Nominatim's
            documentation for `structured requests`:

                https://nominatim.org/release-docs/develop/api/Search

        :type query: dict or str

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param int limit: Maximum amount of results to return from Nominatim.
            Unless exactly_one is set to False, limit will always be 1.

        :param bool addressdetails: If you want in *Location.raw* to include
            address details such as house_number, city_district, postcode, etc
            (in a structured form) set it to True

        :param str language: Preferred language in which to return results.
            Either uses standard
            `RFC2616 <http://www.ietf.org/rfc/rfc2616.txt>`_
            accept-language string or a simple comma-separated
            list of language codes.

        :param str geometry: If present, specifies whether the geocoding
            service should return the result's geometry in `wkt`, `svg`,
            `kml`, or `geojson` formats. This is available via the
            `raw` attribute on the returned :class:`geopy.location.Location`
            object.

        :param bool extratags: Include additional information in the result if available,
            e.g. wikipedia link, opening hours.

        :param country_codes: Limit search results
            to a specific country (or a list of countries).
            A country_code should be the ISO 3166-1alpha2 code,
            e.g. ``gb`` for the United Kingdom, ``de`` for Germany, etc.

        :type country_codes: str or list

        :type viewbox: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.

        :param viewbox: Prefer this area to find search results. By default this is
            treated as a hint, if you want to restrict results to this area,
            specify ``bounded=True`` as well.
            Example: ``[Point(22, 180), Point(-22, -180)]``.

        :param bool bounded: Restrict the results to only items contained
            within the bounding ``viewbox``.

        :param str featuretype: If present, restrict results to certain type of features.
            Allowed values: `country`, `state`, `city`, `settlement`.

        :param bool namedetails: If you want in *Location.raw* to include
            namedetails, set it to True. This will be a list of alternative names,
            including language variants, etc.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """

        if isinstance(query, collections.abc.Mapping):
            params = {
                key: val
                for key, val
                in query.items()
                if key in self.structured_query_params
            }
        else:
            params = {'q': query}

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

        if viewbox:
            params['viewbox'] = self._format_bounding_box(
                viewbox, "%(lon1)s,%(lat1)s,%(lon2)s,%(lat2)s")

        if bounded:
            params['bounded'] = 1

        if not country_codes:
            country_codes = []
        if isinstance(country_codes, str):
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
            params['featureType'] = featuretype

        url = self._construct_url(self.api, params)
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
            addressdetails=True,
            zoom=None,
            namedetails=False,
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

        :param bool addressdetails: Whether or not to include address details,
            such as city, county, state, etc. in *Location.raw*

        :param int zoom: Level of detail required for the address,
            an integer in range from 0 (country level) to 18 (building level),
            default is 18.

        :param bool namedetails: If you want in *Location.raw* to include
            namedetails, set it to True. This will be a list of alternative names,
            including language variants, etc.

            .. versionadded:: 2.3

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

        if zoom is not None:
            params['zoom'] = zoom

        if namedetails:
            params['namedetails'] = 1

        url = self._construct_url(self.reverse_api, params)
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_code(self, place):
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

        if isinstance(places, collections.abc.Mapping) and 'error' in places:
            if places['error'] == 'Unable to geocode':
                # no results in reverse
                return None
            else:
                raise GeocoderQueryError(places['error'])

        if not isinstance(places, collections.abc.Sequence):
            places = [places]
        if exactly_one:
            return self._parse_code(places[0])
        else:
            return [self._parse_code(place) for place in places]
