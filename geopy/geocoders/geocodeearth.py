from geopy.geocoders.base import DEFAULT_SENTINEL
from geopy.geocoders.pelias import Pelias

__all__ = ("GeocodeEarth", )


class GeocodeEarth(Pelias):
    """geocode.earth, a Pelias-based service provided by the developers
    of Pelias itself.

    .. versionadded:: 1.15.0
    """

    def __init__(
            self,
            api_key,
            format_string=None,
            boundary_rect=None,
            country_bias=None,
            domain='api.geocode.earth',
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            scheme=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """
        :param str api_key: Geocode.earth API key, required.

        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

        :param tuple boundary_rect: Coordinates to restrict search within,
            given as (west, south, east, north) coordinate tuple.

        :param str country_bias: Bias results to this country (ISO alpha-3).

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

        """
        super(GeocodeEarth, self).__init__(
            api_key=api_key,
            format_string=format_string,
            boundary_rect=boundary_rect,
            country_bias=country_bias,
            domain=domain,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            scheme=scheme,
            ssl_context=ssl_context,
        )
