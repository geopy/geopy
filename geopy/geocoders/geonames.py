from functools import partial
from urllib.parse import urlencode

from geopy.exc import (
    GeocoderAuthenticationFailure,
    GeocoderInsufficientPrivileges,
    GeocoderQueryError,
    GeocoderQuotaExceeded,
    GeocoderServiceError,
)
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.timezone import (
    ensure_pytz_is_installed,
    from_fixed_gmt_offset,
    from_timezone_name,
)
from geopy.util import logger

__all__ = ("GeoNames", )


class GeoNames(Geocoder):
    """GeoNames geocoder.

    Documentation at:
        http://www.geonames.org/export/geonames-search.html

    Reverse geocoding documentation at:
        http://www.geonames.org/export/web-services.html#findNearbyPlaceName
    """

    geocode_path = '/searchJSON'
    reverse_path = '/findNearbyPlaceNameJSON'
    reverse_nearby_path = '/findNearbyJSON'
    timezone_path = '/timezoneJSON'

    def __init__(
            self,
            username,
            *,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None,
            scheme='http'
    ):
        """

        :param str username: GeoNames username, required. Sign up here:
            http://www.geonames.org/login

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str user_agent:
            See :attr:`geopy.geocoders.options.default_user_agent`.

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.

        :param callable adapter_factory:
            See :attr:`geopy.geocoders.options.default_adapter_factory`.

            .. versionadded:: 2.0

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`. Note that
            at the time of writing GeoNames doesn't support `https`, so
            the default scheme is `http`. The value of
            :attr:`geopy.geocoders.options.default_scheme` is not respected.
            This parameter is present to make it possible to switch to
            `https` once GeoNames adds support for it.
        """
        super().__init__(
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )
        self.username = username

        domain = 'api.geonames.org'
        self.api = (
            "%s://%s%s" % (self.scheme, domain, self.geocode_path)
        )
        self.api_reverse = (
            "%s://%s%s" % (self.scheme, domain, self.reverse_path)
        )
        self.api_reverse_nearby = (
            "%s://%s%s" % (self.scheme, domain, self.reverse_nearby_path)
        )
        self.api_timezone = (
            "%s://%s%s" % (self.scheme, domain, self.timezone_path)
        )

    def geocode(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            country=None,
            country_bias=None
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

        :param country: Limit records to the specified countries.
            Two letter country code ISO-3166 (e.g. ``FR``). Might be
            a single string or a list of strings.
        :type country: str or list

        :param str country_bias: Records from the country_bias are listed first.
            Two letter country code ISO-3166.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = [
            ('q', query),
            ('username', self.username),
        ]

        if country_bias:
            params.append(('countryBias', country_bias))

        if not country:
            country = []
        if isinstance(country, str):
            country = [country]
        for country_item in country:
            params.append(('country', country_item))

        if exactly_one:
            params.append(('maxRows', 1))
        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            feature_code=None,
            lang=None,
            find_nearby_type='findNearbyPlaceName'
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

        :param str feature_code: A GeoNames feature code

        :param str lang: language of the returned ``name`` element (the pseudo
            language code 'local' will return it in local language)
            Full list of supported languages can be found here:
            https://www.geonames.org/countries/

        :param str find_nearby_type: A flag to switch between different
            GeoNames API endpoints. The default value is ``findNearbyPlaceName``
            which returns the closest populated place. Another currently
            implemented option is ``findNearby`` which returns
            the closest toponym for the lat/lng query.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """

        try:
            lat, lng = self._coerce_point_to_string(query).split(',')
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")

        if find_nearby_type == 'findNearbyPlaceName':  # default
            if feature_code:
                raise ValueError(
                    "find_nearby_type=findNearbyPlaceName doesn't support "
                    "the `feature_code` param"
                )
            params = self._reverse_find_nearby_place_name_params(
                lat=lat,
                lng=lng,
                lang=lang,
            )
            url = "?".join((self.api_reverse, urlencode(params)))
        elif find_nearby_type == 'findNearby':
            if lang:
                raise ValueError(
                    "find_nearby_type=findNearby doesn't support the `lang` param"
                )
            params = self._reverse_find_nearby_params(
                lat=lat,
                lng=lng,
                feature_code=feature_code,
            )
            url = "?".join((self.api_reverse_nearby, urlencode(params)))
        else:
            raise GeocoderQueryError(
                '`%s` find_nearby_type is not supported by geopy' % find_nearby_type
            )

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _reverse_find_nearby_params(self, lat, lng, feature_code):
        params = {
            'lat': lat,
            'lng': lng,
            'username': self.username,
        }
        if feature_code:
            params['featureCode'] = feature_code
        return params

    def _reverse_find_nearby_place_name_params(self, lat, lng, lang):
        params = {
            'lat': lat,
            'lng': lng,
            'username': self.username,
        }
        if lang:
            params['lang'] = lang
        return params

    def reverse_timezone(self, query, *, timeout=DEFAULT_SENTINEL):
        """
        Find the timezone for a point in `query`.

        GeoNames always returns a timezone: if the point being queried
        doesn't have an assigned Olson timezone id, a ``pytz.FixedOffset``
        timezone is used to produce the :class:`geopy.timezone.Timezone`.

        :param query: The coordinates for which you want a timezone.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: :class:`geopy.timezone.Timezone`.
        """
        ensure_pytz_is_installed()

        try:
            lat, lng = self._coerce_point_to_string(query).split(',')
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")

        params = {
            "lat": lat,
            "lng": lng,
            "username": self.username,
        }

        url = "?".join((self.api_timezone, urlencode(params)))

        logger.debug("%s.reverse_timezone: %s", self.__class__.__name__, url)
        return self._call_geocoder(url, self._parse_json_timezone, timeout=timeout)

    def _raise_for_error(self, body):
        err = body.get('status')
        if err:
            code = err['value']
            message = err['message']
            # http://www.geonames.org/export/webservice-exception.html
            if message.startswith("user account not enabled to use"):
                raise GeocoderInsufficientPrivileges(message)
            if code == 10:
                raise GeocoderAuthenticationFailure(message)
            if code in (18, 19, 20):
                raise GeocoderQuotaExceeded(message)
            raise GeocoderServiceError(message)

    def _parse_json_timezone(self, response):
        self._raise_for_error(response)

        timezone_id = response.get("timezoneId")
        if timezone_id is None:
            # Sometimes (e.g. for Antarctica) GeoNames doesn't return
            # a `timezoneId` value, but it returns GMT offsets.
            # Apparently GeoNames always returns these offsets -- for
            # every single point on the globe.
            raw_offset = response["rawOffset"]
            return from_fixed_gmt_offset(raw_offset, raw=response)
        else:
            return from_timezone_name(timezone_id, raw=response)

    def _parse_json(self, doc, exactly_one):
        """
        Parse JSON response body.
        """
        places = doc.get('geonames', [])
        self._raise_for_error(doc)
        if not len(places):
            return None

        def parse_code(place):
            """
            Parse each record.
            """
            latitude = place.get('lat', None)
            longitude = place.get('lng', None)
            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)
            else:
                return None

            placename = place.get('name')
            state = place.get('adminName1', None)
            country = place.get('countryName', None)

            location = ', '.join(
                [x for x in [placename, state, country] if x]
            )

            return Location(location, (latitude, longitude), place)

        if exactly_one:
            return parse_code(places[0])
        else:
            return [parse_code(place) for place in places]
