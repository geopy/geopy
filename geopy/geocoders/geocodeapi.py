from geopy.geocoders.base import Geocoder, DEFAULT_SENTINEL

from geopy.exc import (
    GeocoderAuthenticationFailure,
    GeocoderNotFound,
    GeocoderServiceError,
)

__all__ = ('GeocodeAPI',)


class GeocodeAPI(Geocoder):
    """Geocoder using the Geocode API.

    Documentation at:
        https://geocodeapi.io/documentation/

    """
    base_api_url = 'https://app.geocodeapi.io/api/v1/'
    geocode_path = 'search'
    reverse_path = 'reverse'

    def __init__(
        self,
        api_key,
        *,
        timeout=DEFAULT_SENTINEL,
        proxies=DEFAULT_SENTINEL,
    ):
        """
        :param str api_key: The API key required by GeocodeFarm
            to perform geocoding requests.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.
        """
        super().__init__(timeout=timeout, proxies=proxies)
        self.api_key = api_key

        self.api_geocode = self.base_api_url + self.geocode_path
        self.api_reverse = self.base_api_url + self.reverse_path
