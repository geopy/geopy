from functools import partial

from geopy.exc import GeocoderAuthenticationFailure
from geopy.exc import GeocoderQueryError
from geopy.exc import GeocoderQuotaExceeded
from geopy.exc import GeocoderServiceError
from geopy.exc import GeocoderTimedOut
from geopy.geocoders.base import DEFAULT_SENTINEL
from geopy.geocoders.base import Geocoder
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
            **({"region": region} if region else {}),
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

        return "?".join((base_api, urlencode(params)))

    def _parse_json(
        self,
        response,
        exactly_one=True,
        status="status",
        address="address",
        location="location",
        lat="lat",
        lng="lng",
    ):
        """
        Returns location, (latitude, longitude) from JSON feed.

        :type response: dict

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """

        self._check_status(response.get(status))
        if response is None or "result" not in response:
            return

        place = self._parse_place(
            response["result"],
            location=location,
            address=address,
            lat=lat,
            lng=lng,
        )
        return place if exactly_one else [place]

    def _parse_place(
        self,
        place,
        address="address",
        location="location",
        lat="lat",
        lng="lng",
    ):
        """
        Get the location, lat, and lng from a single JSON place.

        :type place: dict

        :rtype: ``None`` or :class:`geopy.location.Location`
        """

        if place is None or address not in place or location not in place:
            return

        return Location(
            place[address],
            self._parse_coordinate(
                place[location],
                lat=lat,
                lng=lng,
            ),
            place,
        )

    def _parse_coordinate(self, location, lat="lat", lng="lng"):
        """
        Get the lat and lng from a single JSON location.

        :type location: dict

        :rtype: tuple of float
        """

        if location is None or lat not in location or lng not in location:
            return (None, None)

        return (location[lat], location[lng])

    def _check_status(self, status):
        """
        Validates error status.

        :type status: int

        Documentation at:
            https://lbs.qq.com/service/webService/webServiceGuide/status
        """

        if status == 0:
            return
        elif status == 110:
            raise GeocoderAuthenticationFailure("Authentication failure.")
        elif status == 111:
            raise GeocoderAuthenticationFailure("Signature verification failed.")
        elif status == 112:
            raise GeocoderAuthenticationFailure("Invalid IP.")
        elif status == 113:
            raise GeocoderAuthenticationFailure("This feature is not authorized.")
        elif status == 120:
            raise GeocoderQuotaExceeded(
                "The number of requests per second has reached the upper limit.",
            )
        elif status == 121:
            raise GeocoderQuotaExceeded(
                "The number of requests daily has reached the upper limit.",
            )
        elif status in 190:
            raise GeocoderAuthenticationFailure("Invalid KEY.")
        elif status == 199:
            raise GeocoderAuthenticationFailure("The webservice isn't enabled.")
        elif status in {301, 311}:
            raise GeocoderQueryError("KEY illegal or not exist.")
        elif status in {300, 306, 301, 320, 330, 331, 348, 351, 394, 395, 399}:
            raise GeocoderQueryError("Invalid parameters.")
        elif status in {347, 393}:
            raise GeocoderQueryError("No results.")
        elif status in {400, 402}:
            raise GeocoderQueryError("Can't decode the request URL.")
        elif status == 404:
            raise GeocoderQueryError("Invalid request path.")
        elif status == 407:
            raise GeocoderQueryError("Invalid request method.")
        elif status == 500:
            raise GeocoderTimedOut("Request timed out.")
        elif 500 < status < 600:
            raise GeocoderServiceError("Request server error.")
        else:
            raise GeocoderQueryError(f"Unknown error. Status: {status}")
