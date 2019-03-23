from geopy.exc import ConfigurationError
from geopy.geocoders.base import DEFAULT_SENTINEL
from geopy.geocoders.osm import Nominatim

__all__ = ("OpenMapQuest", )


class OpenMapQuest(Nominatim):
    """Geocoder using MapQuest Open Platform Web Services.

    Documentation at:
        https://developer.mapquest.com/documentation/open/

    .. versionchanged:: 1.17.0
       OpenMapQuest now extends the Nominatim class.
    """

    geocode_path = '/nominatim/v1/search'
    reverse_path = '/nominatim/v1/reverse'

    def __init__(
            self,
            api_key=None,
            format_string=None,
            view_box=None,
            bounded=None,
            country_bias=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            domain='open.mapquestapi.com',
            scheme=None,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """

        :param str api_key: API key provided by MapQuest, required.

            .. versionchanged:: 1.12.0
               OpenMapQuest now requires an API key. Using an empty key will
               result in a :class:`geopy.exc.ConfigurationError`.

        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

        :type view_box: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.
        :param view_box: Coordinates to restrict search within.
            Example: ``[Point(22, 180), Point(-22, -180)]``.

            .. versionadded:: 1.17.0

            .. deprecated:: 1.19.0
                This argument will be removed in geopy 2.0.
                Use `geocode`'s `viewbox` instead.

        :param bool bounded: Restrict the results to only items contained
            within the bounding view_box.

            .. versionadded:: 1.17.0

            .. deprecated:: 1.19.0
                This argument will be removed in geopy 2.0.
                Use `geocode`'s `bounded` instead.

        :type country_bias: str or list
        :param country_bias: Limit search results to a specific country.
            This param sets a default value for the `geocode`'s ``country_codes``.

            .. versionadded:: 1.17.0

            .. deprecated:: 1.19.0
                This argument will be removed in geopy 2.0.
                Use `geocode`'s `country_codes` instead.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str domain: Domain where the target Nominatim service
            is hosted.

            .. versionadded:: 1.17.0

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`.

        :param str user_agent:
            See :attr:`geopy.geocoders.options.default_user_agent`.

            .. versionadded:: 1.12.0

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.

            .. versionadded:: 1.14.0
        """
        super(OpenMapQuest, self).__init__(
            format_string=format_string,
            view_box=view_box,
            bounded=bounded,
            country_bias=country_bias,
            timeout=timeout,
            proxies=proxies,
            domain=domain,
            scheme=scheme,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )
        if not api_key:
            raise ConfigurationError('OpenMapQuest requires an API key')
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
        return super(OpenMapQuest, self)._construct_url(base_api, params)
