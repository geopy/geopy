from geopy.geocoders import Nominatim
from geopy.geocoders.base import DEFAULT_SENTINEL

__all__ = ("PickPoint",)


class PickPoint(Nominatim):
    """PickPoint geocoder is a commercial version of Nominatim.

    Documentation at:
       https://pickpoint.io/api-reference

    .. versionadded:: 1.13.0

    """

    geocode_path = '/v1/forward'
    reverse_path = '/v1/reverse'

    def __init__(
            self,
            api_key,
            format_string=None,
            view_box=None,
            bounded=None,
            country_bias=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            domain='api.pickpoint.io',
            scheme=None,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """

        :param str api_key: PickPoint API key obtained at
            https://pickpoint.io.

        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

        :type view_box: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.
        :param view_box: Coordinates to restrict search within.
            Example: ``[Point(22, 180), Point(-22, -180)]``.

            .. versionchanged:: 1.17.0
                Previously view_box could be a list of 4 strings or numbers
                in the format of ``[longitude, latitude, longitude, latitude]``.
                This format is now deprecated in favor of a list/tuple
                of a pair of geopy Points and will be removed in geopy 2.0.

            .. deprecated:: 1.19.0
                This argument will be removed in geopy 2.0.
                Use `geocode`'s `viewbox` instead.

        :param bool bounded: Restrict the results to only items contained
            within the bounding view_box.

            .. deprecated:: 1.19.0
                This argument will be removed in geopy 2.0.
                Use `geocode`'s `bounded` instead.

        :type country_bias: str or list
        :param country_bias: Limit search results to a specific country.
            This param sets a default value for the `geocode`'s ``country_codes``.

            .. deprecated:: 1.19.0
                This argument will be removed in geopy 2.0.
                Use `geocode`'s `country_codes` instead.

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

            .. versionadded:: 1.14.0
        """

        super(PickPoint, self).__init__(
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
        return super(PickPoint, self)._construct_url(base_api, params)
