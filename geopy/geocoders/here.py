"""
:class:`.Here` geocoder.
"""

from geopy.compat import urlencode
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

__all__ = ("Here", )


class Here(Geocoder):
    """Geocoder using the HERE Geocoder API.

    Documentation at:
        https://developer.here.com/documentation/geocoder/
    """

    structured_query_params = {
        'city',
        'county',
        'district',
        'country',
        'state',
        'street',
        'housenumber',
        'postalcode',
    }

    def __init__(
            self,
            app_id,
            app_code,
            format_string=None,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """

        :param str app_id: Should be a valid HERE Maps APP ID
            See https://developer.here.com/authenticationpage.

        :param str app_code: Should be a valid HERE Maps APP CODE
            See https://developer.here.com/authenticationpage.

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

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.
        """
        super(Here, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )
        self.app_id = app_id
        self.app_code = app_code
        self.api = "%s://geocoder.api.here.com/6.2/geocode.json" % self.scheme
        self.reverse_api = "%s://reverse.geocoder.api.here.com/6.2/reversegeocode.json" \
            % self.scheme
        # FIXME(?): add multi-reverse geocode
        # FIXME(?): add landmark geocode

    def geocode(
            self,
            query,
            exactly_one=True,
            language=None,
            additional_data=False,
            other=None,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return a location point by address.

        Documentation at:
            https://developer.here.com/documentation/geocoder/topics/resource-geocode.html

        :param str query: The address or query you wish to geocode.

            For a structured query, provide a dictionary whose keys
            are one of: `city`, `county`, `district`, `country`, `state`,
            `street`, `housenumber`, or `postalcode`.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param str language: Affects the language of the response,
            must be a RFC 4647 language code, e.g. 'en-US'.

        :param str additional_data: A string with key-value pairs as described on
            https://developer.here.com/documentation/geocoder/topics/resource-params-additional.html.
            These will be added as one query parameter to the URL.

        :param dict other: A dictionary with additional key/values as described
            in the online documentation. These will be added as individual query
            parameters to the URL.

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
            params['app_id'] = self.app_id
            params['app_code'] = self.app_code
        else:
            params = {
                'searchtext': self.format_string % query,
                'app_id': self.app_id,
                'app_code': self.app_code
            }
        if exactly_one:
            params['maxresults'] = 1
        if language:
            params['language'] = language
        if additional_data:
            params['additionaldata'] = additional_data
        if other:
            params.update(other)

        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one
        )

    def reverse(
            self,
            query,
            exactly_one=True,
            language=None,
            other=None,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return an address by location point.

        Documentation at:
            https://developer.here.com/documentation/geocoder/topics/resource-reverse-geocode.html

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

        :param str language: Affects the language of the response,
            must be a RFC 4647 language code, e.g. 'en-US'.

        :param dict other: A dictionary with additional key/values as described
            in the online documentation. These will be added as individual query
            parameters to the URL.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        point = self._coerce_point_to_string(query)
        params = {
            'app_id': self.app_id,
            'app_code': self.app_code,
            'maxresults': 1,
            'mode': 'retrieveAddresses',  # can be overwritten using `other`
            'prox': point + ',1000',
        }
        if exactly_one:
            params['maxresults'] = 1
        if language:
            params['language'] = language
        if other:
            params.update(other)

        url = "%s?%s" % (
            self.reverse_api, urlencode(params))
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

        try:
            resources = doc['Response']['View'][0]['Result']
        except IndexError:
            resources = None
        if resources is None or not len(resources):
            return None

        def parse_resource(resource):
            """
            Parse each return object.
            """
            stripchars = ", \n"
            addr = resource['Location']['Address']

            address = addr.get('Label', '').strip(stripchars)
            city = addr.get('City', '').strip(stripchars)
            state = addr.get('State', '').strip(stripchars)
            zipcode = addr.get('PostalCode', '').strip(stripchars)
            country = addr.get('Country', '').strip(stripchars)

            city_state = join_filter(", ", [city, state])
            place = join_filter(" ", [city_state, zipcode])
            location = join_filter(", ", [address, place, country])

            display_pos = resource['Location']['DisplayPosition']
            latitude = display_pos['Latitude'] or None
            longitude = display_pos['Longitude'] or None
            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)

            return Location(location, (latitude, longitude), resource)

        if exactly_one:
            return parse_resource(resources[0])
        else:
            return [parse_resource(resource) for resource in resources]
