from geopy.geocoders.base import DEFAULT_SENTINEL
from geopy.geocoders.nominatim import Nominatim

__all__ = ("OpenMapQuest", )


class OpenMapQuest(Nominatim):
    """Geocoder using MapQuest Open Platform Web Services.

    Documentation at:
        https://developer.mapquest.com/documentation/open/

    MapQuest provides two Geocoding APIs:

    - :class:`geopy.geocoders.OpenMapQuest` (this class) Nominatim-alike API
      which is based on Open data from OpenStreetMap.
    - :class:`geopy.geocoders.MapQuest` MapQuest's own API which is based on
      Licensed data.
    """

    geocode_path = '/nominatim/v1/search'
    reverse_path = '/nominatim/v1/reverse'

    def __init__(
            self,
            api_key,
            *,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            domain='open.mapquestapi.com',
            scheme=None,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """

        :param str api_key: API key provided by MapQuest, required.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str domain: Domain where the target Nominatim service
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

            .. versionadded:: 2.0
        """
        super().__init__(
            timeout=timeout,
            proxies=proxies,
            domain=domain,
            scheme=scheme,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )
        self.api_key = api_key

    def _construct_url(self, base_api, params):
        """
        Construct geocoding request url. Overridden.

        :param str base_api: Geocoding function base address - self.api
            or self.reverse_api.

        :param dict params: Geocoding params.

        :return: string URL.
        """
        params['key'] = self.api_key
        return super()._construct_url(base_api, params)
