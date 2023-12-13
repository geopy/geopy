import collections.abc
from functools import partial
from urllib.parse import urlencode

from geopy.exc import GeocoderQueryError
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("Geoapify",)

_DEFAULT_GEOAPIFY_DOMAIN = "api.geoapify.com"


class Geoapify(Geocoder):
    """Geoapify geocoder.

    Documentatin at:
        https://apidocs.geoapify.com/docs/geocoding/forward-geocoding/

    .. attention::
       The free tier allows up to 5 requests/second, and up to 3000
       credits per day. The FAQ explains how to convert credit to requests.
       As of 2023, 1 Geocoding API request is 1 credit.

       Having an API key is mandatory even for the free tier.

       https://www.geoapify.com/pricing

    """

    structured_query_params = {
        "name",
        "housenumber",
        "street",
        "postcode",
        "city",
        "state",
        "country",
    }

    api_version = "/v1"
    geocode_path = "/search"
    reverse_path = "/reverse"

    def __init__(
        self,
        api_key,
        *,
        timeout=DEFAULT_SENTINEL,
        proxies=DEFAULT_SENTINEL,
        domain=_DEFAULT_GEOAPIFY_DOMAIN,
        scheme=None,
        user_agent=None,
        ssl_context=DEFAULT_SENTINEL,
        adapter_factory=None,
    ):
        """
        :param str api_key:
            API key given by Geoapify.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str domain: Domain where the target Geoapify service
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

        """

        super().__init__(
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )

        self.domain = domain.strip("/")
        self._base_url = f"{self.scheme}://{self.domain}{self.api_version}/geocode"

        self.geocode_url = f"{self._base_url}{self.geocode_path}"
        self.reverse_url = f"{self._base_url}{self.reverse_path}"

        self.api_key = api_key

    def geocode(
        self,
        query,
        *,
        exactly_one=True,
        timeout=DEFAULT_SENTINEL,
        limit=None,
        lang=None,
        filter_=False,
        bias=False,
    ):
        """
        Return a location point by address.

        :param query: The address, query or a structured query
            you wish to geocode.

            For a structured query, provide a dictionary whose keys
            are one of: ``name``, ``housenumber``, ``street``, ``postcode``,
            ``city``, ``state``, ``country``. For more information, see Geoapify's
            documentation for structured address:

                https://apidocs.geoapify.com/docs/geocoding/forward-geocoding/#about

            If used as str, the ``text`` key for Free-form adress is used.

        :type query: dict or str

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param int limit: Maximum amount of results to return from Geoapify.
            Unless ``exactly_one`` is set to ``False``, limit will always be 1.

        :param str lang: Result language. 2-character ISO 639-1 language
            codes are supported.
            e.g. ``lang=fr``

        :param str filter_: Filter places by country, boundary, circle.
            See the Location Filters section in Geoapify doc for more details.
            This will be translated to `filter` in the query parameter.
            e.g. ``filter_="rect:-122.569140,37.936672,-122.5324795,37.9588474"``

        :param str bias: Prefer places by ``country``, ``boundary``,
            ``circle``, ``location``. See the Location Bias section in Geoapify
            doc for more details.
            e.g. ``bias="proximity:-122.52985959,37.95335060"``

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = (
            {k: v for k, v in query.items() if k in self.structured_query_params}
            if isinstance(query, collections.abc.Mapping)
            else {"text": query}
        )

        params["apiKey"] = self.api_key
        params["format"] = "json"

        params = self._parse_keyword_params(
            params,
            exactly_one=exactly_one,
            limit=limit,
            lang=lang,
            filter_=filter_,
            bias=bias,
        )

        url = self._construct_url(self.geocode_url, params)
        logger.debug(f"{self.__class__.__name__}.geocode: {url}")
        callback = partial(self._parse_json, exactly_one=exactly_one)

        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(
        self,
        query,
        *,
        exactly_one=True,
        timeout=DEFAULT_SENTINEL,
        limit=None,
        lang=None,
        type_=None,
    ):
        """
        Return an address by location point.

        Documentation at:
            https://apidocs.geoapify.com/docs/geocoding/reverse-geocoding/

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

        :param int limit: Maximum amount of results to return from Geoapify.
            Unless ``exactly_one`` is set to ``False``, limit will always be 1.

        :param str lang: Result language. 2-character ISO 639-1 language
            codes are supported.
            e.g. ``lang=fr``

        :param str type_: 	Location type. Possible values supported by Geoapify:
            ``country``, ``state``, ``city``, ``postcode``, ``street``, ``amenity``.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        try:
            lat, lon = self._coerce_point_to_string(query).split(",")
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")

        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
        }

        params["apiKey"] = self.api_key

        params = self._parse_keyword_params(
            params,
            exactly_one=exactly_one,
            limit=limit,
            lang=lang,
            type_=type_,
        )

        url = self._construct_url(self.reverse_url, params)
        logger.debug(f"{self.__class__.__name__}.geocode: {url}")
        callback = partial(self._parse_json, exactly_one=exactly_one)

        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_keyword_params(self, params, **kwargs):
        """Helper method for adding parameters to params dict before making
        the url"""

        limit = kwargs.get("limit")
        exactly_one = kwargs.get("exactly_one")

        if exactly_one:
            params["limit"] = 1
        elif limit:
            limit = int(limit)
            if limit < 1:
                raise ValueError("Limit cannot be less than 1")
            params["limit"] = limit

        for arg in ("lang", "bias", "filter_", "type_"):
            value = kwargs.get(arg)

            if value:
                if arg.endswith("_"):
                    arg = arg[:-1]
                params[arg] = value

        return params

    def _construct_url(self, url, params):
        """Construct URL for request

        :param str base_api: Geocoding function base address - self.geocode_url
            or self.reverse_url.

        :param dict params: query params.

        :return: string URL.
        """
        return "?".join((url, urlencode(params)))

    def _parse_json(self, results, exactly_one):
        """Parse results returned by API"""
        if not results:
            return None

        if results.get("error"):
            raise GeocoderQueryError(str(results))

        results = results.get("results", [])
        if not len(results):
            return None

        if exactly_one:
            return self._parse_result(results[0])

        return [self._parse_result(result) for result in results]

    def _parse_result(self, result):
        """Parse each result from ``_parse_json``"""
        location = result.get("formatted")
        latitude = result.get("lat")
        longitude = result.get("lon")

        return Location(location, (latitude, longitude), result)
