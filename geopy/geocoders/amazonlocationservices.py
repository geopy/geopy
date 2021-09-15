import importlib
from copy import copy

from geopy.exc import GeocoderTimedOut
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location

__all__ = ("AmazonLocationServices",)


class AmazonLocationServices(Geocoder):
    """Amazon Location Services geocoder.

    Documentation at:
        https://docs.aws.amazon.com/location-places/latest/APIReference/Welcome.html
    """

    def __init__(
        self,
        *,
        retries=0,
        scheme=None,
        timeout=DEFAULT_SENTINEL,
        proxies=DEFAULT_SENTINEL,
        user_agent=None,
        ssl_context=DEFAULT_SENTINEL,
        adapter_factory=None,
    ):
        """
        :param ing retries: Number of times to retry a request.
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
            .. versionadded:: 2.0
        """
        self._boto3 = importlib.import_module("boto3")
        self._Config = importlib.import_module("botocore.config").Config
        self._ReadTimeoutError = importlib.import_module(
            "botocore.exceptions"
        ).ReadTimeoutError

        super().__init__(
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )

        self._config = self._Config(
            retries={"total_max_attempts": retries + 1, "mode": "standard"},
        )
        if timeout is not DEFAULT_SENTINEL:
            self._config.read_timeout = timeout

        self.client = self._boto3.client(
            "location",
            config=self._config,
        )

    def geocode(
        self,
        query,
        *,
        index_name,
        filter_countries=None,
        exactly_one=True,
        max_results=50,
        timeout=DEFAULT_SENTINEL,
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.
        :param str index_name: The name of the PlaceIndex to query (created in
            Amazon Location Services).
        :param str filter_countries: Bias results to this country (ISO alpha-3).
        :param bool exactly_one: Return one result or a list of results, if
            available.
        :param int max_results: Limit the number of results returned, only applies
            if :paramref:`exactly_one` is ``False``.
        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization. NB: This
            will create a new client with the timeout config.
        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """

        # Create a new client for this request only, it will be thrown away at
        # the end.
        if not (timeout is DEFAULT_SENTINEL):
            config = copy(self._config)
            config.read_timeout = timeout
            req_client = self._boto3.client("location", config=config)
        # Otherwise use the initialised client.
        else:
            req_client = self.client

        params = {
            "Text": query,
            "IndexName": index_name,
            "MaxResults": max_results,
        }

        if filter_countries:
            params["FilterCountries"] = filter_countries

        try:
            response = req_client.search_place_index_for_text(**params)
        except self._ReadTimeoutError as exc:
            raise GeocoderTimedOut(
                "Geocoder timed out waiting for a response, try increasing the "
                "timeout value."
            ) from exc

        return self._parse_json(response=response, exactly_one=exactly_one)

    def _parse_code(self, result):
        place = result.get("Place", {})
        geometry = place.get("Geometry", {})
        point = geometry.get("Point", [])

        if len(point) != 2:
            raise AssertionError("Point is empty, or it is a WGS84 point (1 number).")

        latitude = point[1]
        longitude = point[0]
        placename = place.get("Label")

        return Location(placename, (latitude, longitude), result)

    def _parse_json(self, response, exactly_one):
        if response is None:
            return None
        results = response["Results"]
        if not len(results):
            return None
        if exactly_one:
            return self._parse_code(results[0])
        else:
            return [self._parse_code(result) for result in results]
