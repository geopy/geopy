from geopy.geocoders import Nominatim
from geopy.geocoders.base import DEFAULT_SENTINEL

__all__ = ("PickPoint",)


class PickPoint(Nominatim):
    """PickPoint geocoder is a commercial version of Nominatim.

    Documentation at:
       https://pickpoint.io/api-reference

    .. versionadded:: 1.13.0

    """

    def __init__(
            self,
            api_key,
            format_string=None,
            view_box=None,
            bounded=False,
            country_bias=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            domain='api.pickpoint.io',
            scheme=None,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """

        :param string api_key: PickPoint API key obtained at
            https://pickpoint.io.

        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

        :param tuple view_box: Coordinates to restrict search within.

        :param string country_bias: Bias results to this country.

        :param bool bounded: Restrict the results to only items contained
            within the bounding view_box.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str domain: Should be the localized Openstreetmap domain to
            connect to. The default is ``'api.pickpoint.io'``, but you
            can change it to a domain of your own.

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
        self.api = "%s://%s/v1/forward" % (self.scheme, self.domain)
        self.reverse_api = "%s://%s/v1/reverse" % (self.scheme, self.domain)

    def _construct_url(self, base_api, params):
        """
        Construct geocoding request url. Overriden.

        :param string base_api: Geocoding function base address - self.api
            or self.reverse_api.

        :param dict params: Geocoding params.

        :return: string URL.
        """
        params['key'] = self.api_key
        return super(PickPoint, self)._construct_url(base_api, params)
