import warnings

from geopy.compat import urlencode
from geopy.exc import (
    ConfigurationError,
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

    .. versionadded:: 1.15.0
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

    geocode_path = '/6.2/geocode.json'
    reverse_path = '/6.2/reversegeocode.json'

    def __init__(
            self,
            app_id=None,
            app_code=None,
            apikey=None,
            format_string=None,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """

        :param str app_id: Should be a valid HERE Maps APP ID. Will eventually
            be replaced with APIKEY.
            See https://developer.here.com/authenticationpage.

            .. deprecated:: 1.21.0
                App ID and App Code are being replaced by API Keys and OAuth 2.0
                by HERE. Consider getting an ``apikey`` instead of using
                ``app_id`` and ``app_code``.

        :param str app_code: Should be a valid HERE Maps APP CODE. Will
            eventually be replaced with APIKEY.
            See https://developer.here.com/authenticationpage.

            .. deprecated:: 1.21.0

        :param str apikey: Should be a valid HERE Maps APIKEY. These keys were
            introduced in December 2019 and will eventually replace the legacy
            APP CODE/APP ID pairs which are already no longer available for new
            accounts (but still work for old accounts).
            More authentication details are available at
            https://developer.here.com/blog/announcing-two-new-authentication-types.
            See https://developer.here.com/authenticationpage.

            .. versionadded:: 1.21.0

        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

            .. deprecated:: 1.22.0

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
        is_apikey = bool(apikey)
        is_app_code = app_id and app_code
        if not is_apikey and not is_app_code:
            raise ConfigurationError(
                "HERE geocoder requires authentication, either `apikey` "
                "or `app_id`+`app_code` must be set"
            )
        if is_app_code:
            warnings.warn(
                'Since December 2019 HERE provides two new authentication '
                'methods `API Key` and `OAuth 2.0`. `app_id`+`app_code` '
                'is deprecated and might eventually be phased out. '
                'Consider switching to `apikey`, which geopy supports. '
                'See https://developer.here.com/blog/announcing-two-new-authentication-types',  # noqa
                UserWarning,
                stacklevel=2
            )

        self.app_id = app_id
        self.app_code = app_code
        self.apikey = apikey
        domain = "ls.hereapi.com" if is_apikey else "api.here.com"
        self.api = "%s://geocoder.%s%s" % (self.scheme, domain, self.geocode_path)
        self.reverse_api = (
            "%s://reverse.geocoder.%s%s" % (self.scheme, domain, self.reverse_path)
        )

    def geocode(
            self,
            query,
            bbox=None,
            mapview=None,
            exactly_one=True,
            maxresults=None,
            pageinformation=None,
            language=None,
            additional_data=False,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return a location point by address.

        This implementation supports only a subset of all available parameters.
        A list of all parameters of the pure REST API is available here:
        https://developer.here.com/documentation/geocoder/topics/resource-geocode.html

        :param str query: The address or query you wish to geocode.

            For a structured query, provide a dictionary whose keys
            are one of: `city`, `county`, `district`, `country`, `state`,
            `street`, `housenumber`, or `postalcode`.

        :param bbox: A type of spatial filter, limits the search for any other attributes
            in the request. Specified by two coordinate (lat/lon)
            pairs -- corners of the box. `The bbox search is currently similar
            to mapview but it is not extended` (cited from the REST API docs).
            Relevant global results are also returned.
            Example: ``[Point(22, 180), Point(-22, -180)]``.
        :type bbox: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.

        :param mapview: The app's viewport, given as two coordinate pairs, specified
            by two lat/lon pairs -- corners of the bounding box,
            respectively. Matches from within the set map view plus an extended area
            are ranked highest. Relevant global results are also returned.
            Example: ``[Point(22, 180), Point(-22, -180)]``.
        :type mapview: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int maxresults: Defines the maximum number of items in the
            response structure. If not provided and there are multiple results
            the HERE API will return 10 results by default. This will be reset
            to one if ``exactly_one`` is True.

        :param int pageinformation: A key which identifies the page to be returned
            when the response is separated into multiple pages. Only useful when
            ``maxresults`` is also provided.

        :param str language: Affects the language of the response,
            must be a RFC 4647 language code, e.g. 'en-US'.

        :param str additional_data: A string with key-value pairs as described on
            https://developer.here.com/documentation/geocoder/topics/resource-params-additional.html.
            These will be added as one query parameter to the URL.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

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
            params = {'searchtext': self.format_string % query}
        if bbox:
            params['bbox'] = self._format_bounding_box(
                bbox, "%(lat2)s,%(lon1)s;%(lat1)s,%(lon2)s")
        if mapview:
            params['mapview'] = self._format_bounding_box(
                mapview, "%(lat2)s,%(lon1)s;%(lat1)s,%(lon2)s")
        if pageinformation:
            params['pageinformation'] = pageinformation
        if maxresults:
            params['maxresults'] = maxresults
        if exactly_one:
            params['maxresults'] = 1
        if language:
            params['language'] = language
        if additional_data:
            params['additionaldata'] = additional_data
        if self.apikey:
            params['apiKey'] = self.apikey
        else:
            params['app_id'] = self.app_id
            params['app_code'] = self.app_code

        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one
        )

    def reverse(
            self,
            query,
            radius=None,
            exactly_one=True,
            maxresults=None,
            pageinformation=None,
            language=None,
            mode='retrieveAddresses',
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return an address by location point.

        This implementation supports only a subset of all available parameters.
        A list of all parameters of the pure REST API is available here:
        https://developer.here.com/documentation/geocoder/topics/resource-reverse-geocode.html

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param float radius: Proximity radius in meters.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int maxresults: Defines the maximum number of items in the
            response structure. If not provided and there are multiple results
            the HERE API will return 10 results by default. This will be reset
            to one if ``exactly_one`` is True.

        :param int pageinformation: A key which identifies the page to be returned
            when the response is separated into multiple pages. Only useful when
            ``maxresults`` is also provided.

        :param str language: Affects the language of the response,
            must be a RFC 4647 language code, e.g. 'en-US'.

        :param str mode: Affects the type of returned response items, must be
            one of: 'retrieveAddresses' (default), 'retrieveAreas', 'retrieveLandmarks',
            'retrieveAll', or 'trackPosition'. See online documentation for more
            information.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        point = self._coerce_point_to_string(query)
        params = {
            'mode': mode,
            'prox': point,
        }
        if radius is not None:
            params['prox'] = '%s,%s' % (params['prox'], float(radius))
        if pageinformation:
            params['pageinformation'] = pageinformation
        if maxresults:
            params['maxresults'] = maxresults
        if exactly_one:
            params['maxresults'] = 1
        if language:
            params['language'] = language
        if self.apikey:
            params['apiKey'] = self.apikey
        else:
            params['app_id'] = self.app_id
            params['app_code'] = self.app_code
        url = "%s?%s" % (self.reverse_api, urlencode(params))
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
        if not resources:
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
            latitude = float(display_pos['Latitude'])
            longitude = float(display_pos['Longitude'])

            return Location(location, (latitude, longitude), resource)

        if exactly_one:
            return parse_resource(resources[0])
        else:
            return [parse_resource(resource) for resource in resources]
