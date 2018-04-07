"""
PickPoint geocoder
"""

from geopy.compat import urlencode
from geopy.geocoders import Nominatim

from geopy.geocoders.base import (
    DEFAULT_FORMAT_STRING,
    DEFAULT_TIMEOUT,
    DEFAULT_SCHEME
)

__all__ = ("PickPoint",)


class PickPoint(Nominatim):
    """
    PickPoint geocoder is a commercial version of Nominatim. Documentation at:
       https://pickpoint.io/api-reference

    .. versionadded:: 1.13.0

    """

    def __init__(
            self,
            api_key,
            format_string=DEFAULT_FORMAT_STRING,
            view_box=None,
            country_bias=None,
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
            domain='api.pickpoint.io',
            scheme=DEFAULT_SCHEME,
            user_agent=None
    ):
        """

        :param string api_key: PickPoint API key obtained at https://pickpoint.io.

        :param string format_string: String containing '%s' where the
            string to geocode should be interpolated before querying the
            geocoder. For example: '%s, Mountain View, CA'. The default
            is just '%s'.

        :param tuple view_box: Coordinates to restrict search within.

        :param string country_bias: Bias results to this country.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

        :param str user_agent: Use a custom User-Agent header.
        """

        super(PickPoint, self).__init__(
            format_string=format_string,
            view_box=view_box,
            country_bias=country_bias,
            timeout=timeout,
            proxies=proxies,
            domain=domain,
            scheme=scheme,
            user_agent=user_agent,
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
