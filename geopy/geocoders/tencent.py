from functools import partial

from geopy.exc import (
    GeocoderAuthenticationFailure,
    GeocoderQueryError,
    GeocoderQuotaExceeded,
    GeocoderServiceError,
    GeocoderTimedOut,
)
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("Tencent",)


class Tencent(Geocoder):
    """
    Geocoder using the Tencent Maps API.

    Documentation at:
        https://lbs.qq.com/service/webService/webServiceGuide/webServiceOverview
    """

    api_path = reverse_path = "/ws/geocoder/v1/"

    def __init__(
        self,
        api_key,
        *,
        scheme=None,
        timeout=DEFAULT_SENTINEL,
        proxies=DEFAULT_SENTINEL,
        user_agent=None,
        ssl_context=DEFAULT_SENTINEL,
        adapter_factory=None,
    ):
        """
        :param str api_key: The API key required by Tencent Map to perform
            geocoding requests. API keys are managed through the Tencent APIs
            console (https://lbs.qq.com/dev/console/application/mine).

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
        self.api_key = api_key
        self.domin = "apis.map.qq.com"
        self.api = f"{self.scheme}://{self.domin}{self.api_path}"
        self.reverse_api = f"{self.scheme}://{self.domin}{self.reverse_path}"

    def geocode(
        self,
        query,
        *,
        region=None,
        exactly_one=True,
        timeout=DEFAULT_SENTINEL,
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

        :param str region: The city of address.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        Documentation at:
            https://lbs.qq.com/service/webService/webServiceGuide/webServiceGeocoder
        """

        params = {
            "address": query,
            "region": region,
            "key": self.api_key,
        }
        url = self._construct_url(self.api, params)

        logger.debug(f"{self.__class__.__name__}.geocode: {url}")
        callback = partial(self._parse_json, exactly_one=exactly_one, address="title")

        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(self, query, *, exactly_one=True, timeout=DEFAULT_SENTINEL):
        """
        Return an address by location point.

        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.
        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.

        :param bool exactly_one: Return one result or a list of results, if
            available. Tencent's API always return at most one result.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        Documentation at:
            https://lbs.qq.com/service/webService/webServiceGuide/webServiceGcoder
        """

        params = {
            "location": self._coerce_point_to_string(query),
            "key": self.api_key,
        }
        url = self._construct_url(self.reverse_api, params)

        logger.debug(f"{self.__class__.__name__}.reverse: {url}")
        callback = partial(self._parse_json, exactly_one=exactly_one)

        return self._call_geocoder(url, callback, timeout=timeout)

    def _construct_url(self, base_api, params) -> str:
        """
        Construct geocoding request url.

        :param str base_api: Geocoding function base address - self.api
            or self.reverse_api.

        :param dict params: Geocoding params.

        :return: string URL.
        """
        from urllib.parse import urlencode

        # Remove empty value item
        params = {k: v for k, v in params.items() if v}
        return "?".join((base_api, urlencode(params)))

    def _parse_json(self, response, exactly_one=True, address="address"):
        """
        Returns location, (latitude, longitude) from JSON feed.

        :type response: dict

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """

        self._check_status(response.get("status"), response.get("message"))
        if response is None:
            return

        place = self._parse_place(response.get("result"), address=address)
        return place if exactly_one else [place]

    def _parse_place(self, place, address="address"):
        """
        Get the location, lat, and lng from a single JSON place.

        :type place: dict

        :rtype: ``None`` or :class:`geopy.location.Location`
        """

        if place is None:
            return

        return Location(
            place.get(address),
            self._parse_coordinate(place.get("location")),
            place,
        )

    def _parse_coordinate(self, location):
        """
        Get the lat and lng from a single JSON location.

        :type location: dict

        :rtype: tuple of float
        """

        if location is None:
            return (None, None)

        return (location.get("lat"), location.get("lng"))

    def _check_status(self, status, message):
        """
        Validates error status.

        :type status: int

        :type message: str

        Documentation at:
            https://lbs.qq.com/service/webService/webServiceGuide/status
        """

        if status == 0:
            return
        elif status == 110:
            raise GeocoderAuthenticationFailure(f"Authentication failure {message}.")
        elif status == 111:
            raise GeocoderAuthenticationFailure(
                f"Signature verification failed {message}."
            )
        elif status == 112:
            raise GeocoderAuthenticationFailure(f"Invalid IP {message}.")
        elif status == 113:
            raise GeocoderAuthenticationFailure(
                f"This feature is not authorized {message}."
            )
        elif status == 120:
            raise GeocoderQuotaExceeded(
                "The number of requests per second has reached the upper limit "
                f"{message!r}.",
            )
        elif status == 121:
            raise GeocoderQuotaExceeded(
                f"The number of requests daily has reached the upper limit {message}.",
            )
        elif status == 190:
            raise GeocoderAuthenticationFailure(f"Invalid KEY {message}.")
        elif status == 199:
            raise GeocoderAuthenticationFailure(
                f"The webservice isn't enabled {message}."
            )
        elif status in {301, 311}:
            raise GeocoderQueryError(f"KEY illegal or not exist {message}.")
        elif status in {300, 306, 301, 320, 330, 331, 348, 351, 394, 395, 399}:
            raise GeocoderQueryError(f"Invalid parameters {message}.")
        elif status in {347, 393}:
            raise GeocoderQueryError(f"No results {message}.")
        elif status in {400, 402}:
            raise GeocoderQueryError(f"Can't decode the request URL {message}.")
        elif status == 404:
            raise GeocoderQueryError(f"Invalid request path {message}.")
        elif status == 407:
            raise GeocoderQueryError(f"Invalid request method {message}.")
        elif status == 500:
            raise GeocoderTimedOut(f"Request timed out {message}.")
        elif 500 < status < 600:
            raise GeocoderServiceError(f"Request server error {message}.")
        else:
            raise GeocoderQueryError(f"Unknown error {message}.")
