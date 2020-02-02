
from geopy.geocoders.base import DEFAULT_SENTINEL
from geopy.geocoders.tomtom import TomTom

__all__ = ("AzureMaps", )


class AzureMaps(TomTom):
    """AzureMaps geocoder based on TomTom.

    Documentation at:
        https://docs.microsoft.com/en-us/azure/azure-maps/index

    .. versionadded:: 1.15.0
    """

    geocode_path = '/search/address/json'
    reverse_path = '/search/address/reverse/json'

    def __init__(
            self,
            subscription_key,
            format_string=None,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            domain='atlas.microsoft.com',
    ):
        """
        :param str subscription_key: Azure Maps subscription key.

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

        :param str domain: Domain where the target Azure Maps service
            is hosted.
        """
        super(AzureMaps, self).__init__(
            api_key=subscription_key,
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            domain=domain,
        )

    def _geocode_params(self, formatted_query):
        return {
            'api-version': '1.0',
            'subscription-key': self.api_key,
            'query': formatted_query,
        }

    def _reverse_params(self, position):
        return {
            'api-version': '1.0',
            'subscription-key': self.api_key,
            'query': position,
        }
