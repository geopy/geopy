from geopy.geocoders.base import DEFAULT_SENTINEL
from geopy.geocoders.pelias import Pelias

__all__ = ("GeocodeEarth", )


class GeocodeEarth(Pelias):
    """Geocode Earth, a Pelias-based service provided by the developers
    of Pelias itself.

    Documentation at:
        https://geocode.earth/docs

    Pricing details:
        https://geocode.earth/#pricing
    """

    def __init__(
            self,
            api_key,
            *,
            domain='api.geocode.earth',
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            scheme=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """
        :param str api_key: Geocode.earth API key, required.

        :param str domain: Specify a custom domain for Pelias API.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str user_agent:
            See :attr:`geopy.geocoders.options.default_user_agent`.

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`.

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.

        :param callable adapter_factory:
            See :attr:`geopy.geocoders.options.default_adapter_factory`.

            .. versionadded:: 2.0

        """
        super().__init__(
            api_key=api_key,
            domain=domain,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            scheme=scheme,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )
