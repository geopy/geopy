import collections.abc
from functools import partial
from urllib.parse import quote, urlencode

from geopy.exc import (
    GeocoderAuthenticationFailure,
    GeocoderInsufficientPrivileges,
    GeocoderRateLimited,
    GeocoderServiceError,
    GeocoderUnavailable,
)
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import join_filter, logger

__all__ = ("GeocodeFarm", )

class GeocodeFarm(Geocoder):
    """
    Geocoder using the Geocode.Farm API for forward and reverse geocoding.

    Forward API Documentation:
      Base URL: GET https://api.geocode.farm/forward/
      Required parameters:
         - key: Your API key.
         - addr: The URL-encoded address.
      Example:
         GET https://api.geocode.farm/forward/?key=YOUR-API-KEY-HERE&addr=30+N+Gould+St,+Ste+R,+Sheridan,+WY+82801+USA

    Reverse API Documentation:
      Base URL: GET https://api.geocode.farm/reverse/
      Required parameters:
         - key: Your API key.
         - lat: Latitude.
         - lon: Longitude.
      Example:
         GET https://api.geocode.farm/reverse/?key=YOUR-API-KEY-HERE&lat=44.7977733966548&lon=-106.954917523499
    """

    forward_path = "/forward/"
    reverse_path = "/reverse/"

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
            domain='api.geocode.farm'
    ):
        """
        :param str api_key: Your Geocode.Farm API key.
        :param str scheme: See :attr:`geopy.geocoders.options.default_scheme`.
        :param int timeout: See :attr:`geopy.geocoders.options.default_timeout`.
        :param dict proxies: See :attr:`geopy.geocoders.options.default_proxies`.
        :param str user_agent: See :attr:`geopy.geocoders.options.default_user_agent`.
        :param ssl_context: See :attr:`geopy.geocoders.options.default_ssl_context`.
        :param callable adapter_factory: See :attr:`geopy.geocoders.options.default_adapter_factory`.
        :param str domain: Base API domain; defaults to "api.geocode.farm".
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
        self.forward_api = f'{self.scheme}://{domain}{self.forward_path}'
        self.reverse_api = f'{self.scheme}://{domain}{self.reverse_path}'

    def geocode(self, query, *, exactly_one=True, timeout=DEFAULT_SENTINEL, **kwargs):
        """
        Forward geocode an address.

        :param query: The address to geocode.
        :type query: str
        :param bool exactly_one: Return one result or a list of results.
        :param int timeout: Timeout for this request.
        :rtype: :class:`geopy.location.Location` or list of them.
        """
        # Geocode.Farm expects a free-form address string via the "addr" parameter.
        if isinstance(query, collections.abc.Mapping):
            # Structured queries are not supported; convert mapping to string.
            query = join_filter(" ", query.values())
        params = {
            'key': self.api_key,
            'addr': query,
        }
        url = "?".join((self.forward_api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(self, query, *, exactly_one=True, timeout=DEFAULT_SENTINEL, **kwargs):
        """
        Reverse geocode a coordinate pair.

        :param query: The coordinates for which to obtain an address.
                      This can be a (lat, lon) tuple, list, or a string "lat, lon".
        :type query: tuple, list or str
        :param bool exactly_one: Return one result or a list of results.
        :param int timeout: Timeout for this request.
        :rtype: :class:`geopy.location.Location` or list of them.
        """
        point = self._coerce_point_to_string(query)
        try:
            lat, lon = [item.strip() for item in point.split(',')]
        except Exception:
            raise GeocoderServiceError("Invalid point format. Should be 'lat, lon'.")
        params = {
            'key': self.api_key,
            'lat': lat,
            'lon': lon,
        }
        # Quote the point to ensure proper URL formatting.
        quoted_point = quote(point.encode('utf-8'))
        url = "?".join((self.reverse_api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_json(self, doc, exactly_one=True):
        """
        Parse a Geocode.Farm JSON response.

        Checks for errors and extracts the result.

        :param dict doc: JSON response from the API.
        :param bool exactly_one: Flag for returning one or multiple results.
        """
        # Although Geocode.Farm does not include a "statusCode" field in the JSON,
        # we include a similar check if such a field is present.
        status_code = doc.get("statusCode", 200)
        if status_code != 200:
            err = doc.get("error_message", "")
            if status_code == 401:
                raise GeocoderAuthenticationFailure(err)
            elif status_code == 402:
                raise GeocoderInsufficientPrivileges(err)
            elif status_code == 429:
                raise GeocoderRateLimited(err)
            elif status_code == 503:
                raise GeocoderUnavailable(err)
            else:
                raise GeocoderServiceError(err)

        # Check the Geocode.Farm-specific status.
        status = doc.get("STATUS", {})
        if status.get("status") != "SUCCESS":
            err = status.get("error_message", "GeocodeFarm request failed")
            # If the API key is not valid, the "key" field will not be "VALID".
            if status.get("key") != "VALID":
                raise GeocoderAuthenticationFailure(err)
            # Otherwise, raise a generic service error.
            raise GeocoderServiceError(err)

        results = doc.get("RESULTS", {})
        result = results.get("result")
        if not result:
            return None

        location = self._parse_result(result)
        if exactly_one:
            return location
        else:
            return [location]

    def _parse_result(self, result):
        """
        Parse an individual result into a Location object.

        Expected structure of result:
            {
                "coordinates": { "lat": "44.7977733966548", "lon": "-106.954917523499" },
                "address": {
                    "full_address": "30 N Gould St, Sheridan, WY 82801, United States",
                    "house_number": "30",
                    "street_name": "N Gould St",
                    "locality": "Sheridan",
                    "admin_2": "Sheridan County",
                    "admin_1": "WY",
                    "country": "United States",
                    "postal_code": "82801"
                },
                "accuracy": "EXACT_MATCH"
            }
        """
        coordinates = result.get("coordinates", {})
        lat = coordinates.get("lat")
        lon = coordinates.get("lon")
        if lat is None or lon is None:
            return None

        address_info = result.get("address", {})
        address_str = address_info.get("full_address")
        if not address_str:
            # Fallback: build an address string from available components.
            components = [
                address_info.get("house_number", ""),
                address_info.get("street_name", ""),
                address_info.get("locality", ""),
                address_info.get("admin_1", ""),
                address_info.get("country", ""),
            ]
            address_str = ", ".join(filter(None, components))
        return Location(address_str, (float(lat), float(lon)), result)
