from geopy.compat import urlencode, quote
from geopy.exc import (
    GeocoderAuthenticationFailure,
    GeocoderInsufficientPrivileges,
    GeocoderQuotaExceeded,
    GeocoderServiceError,
    GeocoderUnavailable,
)
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import join_filter, logger

__all__ = ("Bing", )


class Bing(Geocoder):
    """Geocoder using the Bing Maps Locations API.

    Documentation at:
        https://msdn.microsoft.com/en-us/library/ff701715.aspx
    """

    structured_query_params = {
        'addressLine',
        'locality',
        'adminDistrict',
        'countryRegion',
        'postalCode',
    }

    geocode_path = '/REST/v1/Locations'
    reverse_path = '/REST/v1/Locations/%(point)s'

    def __init__(
            self,
            api_key,
            format_string=None,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """

        :param str api_key: Should be a valid Bing Maps API key
            (https://www.microsoft.com/en-us/maps/create-a-bing-maps-key).

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
        super(Bing, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )
        self.api_key = api_key
        domain = 'dev.virtualearth.net'
        self.geocode_api = '%s://%s%s' % (self.scheme, domain, self.geocode_path)
        self.reverse_api = '%s://%s%s' % (self.scheme, domain, self.reverse_path)

    def geocode(
            self,
            query,
            exactly_one=True,
            user_location=None,
            timeout=DEFAULT_SENTINEL,
            culture=None,
            include_neighborhood=None,
            include_country_code=False
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

            For a structured query, provide a dictionary whose keys
            are one of: `addressLine`, `locality` (city),
            `adminDistrict` (state), `countryRegion`, or `postalcode`.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param user_location: Prioritize results closer to
            this location.
        :type user_location: :class:`geopy.point.Point`

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param str culture: Affects the language of the response,
            must be a two-letter country code.

            .. versionadded:: 1.4.0

        :param bool include_neighborhood: Sets whether to include the
            neighborhood field in the response.

            .. versionadded:: 1.4.0

        :param bool include_country_code: Sets whether to include the
            two-letter ISO code of the country in the response (field name
            'countryRegionIso2').

            .. versionadded:: 1.4.0

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
            params['key'] = self.api_key
        else:
            params = {
                'query': self.format_string % query,
                'key': self.api_key
            }
        if user_location:
            params['userLocation'] = ",".join(
                (str(user_location.latitude), str(user_location.longitude))
            )
        if exactly_one:
            params['maxResults'] = 1
        if culture:
            params['culture'] = culture
        if include_neighborhood is not None:
            params['includeNeighborhood'] = include_neighborhood
        if include_country_code:
            params['include'] = 'ciso2'  # the only acceptable value

        url = "?".join((self.geocode_api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one
        )

    def reverse(
            self,
            query,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            culture=None,
            include_country_code=False
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

        :param str culture: Affects the language of the response,
            must be a two-letter country code.

        :param bool include_country_code: Sets whether to include the
            two-letter ISO code of the country in the response (field name
            'countryRegionIso2').

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        point = self._coerce_point_to_string(query)
        params = {'key': self.api_key}
        if culture:
            params['culture'] = culture
        if include_country_code:
            params['include'] = 'ciso2'  # the only acceptable value

        quoted_point = quote(point.encode('utf-8'))
        url = "?".join((self.reverse_api % dict(point=quoted_point),
                        urlencode(params)))

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one
        )

    @staticmethod
    def _parse_json(doc, exactly_one=True):
        """
        Parse a location name, latitude, and longitude from an JSON response.
        """
        status_code = doc.get("statusCode", 200)
        if status_code != 200:
            err = doc.get("errorDetails", "")
            if status_code == 401:
                raise GeocoderAuthenticationFailure(err)
            elif status_code == 403:
                raise GeocoderInsufficientPrivileges(err)
            elif status_code == 429:
                raise GeocoderQuotaExceeded(err)
            elif status_code == 503:
                raise GeocoderUnavailable(err)
            else:
                raise GeocoderServiceError(err)

        resources = doc['resourceSets'][0]['resources']
        if resources is None or not len(resources):
            return None

        def parse_resource(resource):
            """
            Parse each return object.
            """
            stripchars = ", \n"
            addr = resource['address']

            address = addr.get('addressLine', '').strip(stripchars)
            city = addr.get('locality', '').strip(stripchars)
            state = addr.get('adminDistrict', '').strip(stripchars)
            zipcode = addr.get('postalCode', '').strip(stripchars)
            country = addr.get('countryRegion', '').strip(stripchars)

            city_state = join_filter(", ", [city, state])
            place = join_filter(" ", [city_state, zipcode])
            location = join_filter(", ", [address, place, country])

            latitude = resource['point']['coordinates'][0] or None
            longitude = resource['point']['coordinates'][1] or None
            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)

            return Location(location, (latitude, longitude), resource)

        if exactly_one:
            return parse_resource(resources[0])
        else:
            return [parse_resource(resource) for resource in resources]
