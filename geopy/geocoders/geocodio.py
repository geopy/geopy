import json
from functools import partial
from urllib.parse import urlencode

from geopy.exc import ConfigurationError, GeocoderQueryError, GeocoderQuotaExceeded
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("Geocodio", )


class Geocodio(Geocoder):
    """Geocoder using the Geocod.io API.

    Documentation at:
        https://www.geocod.io/docs/

    Pricing details:
        https://www.geocod.io/pricing/

    """

    domain = 'api.geocod.io'
    geocode_path = '/v1.6/geocode'
    reverse_path = '/v1.6/reverse'

    def __init__(
        self,
        api_key=None,
        *,
        scheme=None,
        timeout=DEFAULT_SENTINEL,
        proxies=DEFAULT_SENTINEL,
        user_agent=None,
        ssl_context=DEFAULT_SENTINEL,
        adapter_factory=None,
    ):
        """

        :param str api_key:
            See :attr:`geopy.geocoders.options.default_scheme`.

        :param str client_id: If using premier, the account client id.

        :param str secret_key: If using premier, the account secret key.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

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
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )
        if api_key is None:
            raise ConfigurationError('Must provide an api_key.')
        self.api_key = api_key

    def geocode(
        self,
        query=None,
        *,
        limit=None,
        exactly_one=True,
        timeout=DEFAULT_SENTINEL,
    ):
        api = '%s://%s%s' % (self.scheme, self.domain, self.geocode_path)

        params = dict(
            q=query,
            api_key=self.api_key
        )
        if limit is not None:
            params['limit'] = limit

        url = "?".join((api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    @staticmethod
    def _parse_json(page, exactly_one=True):
        """Returns location, (latitude, longitude) from json feed."""

        places = page.get('results', [])

        def parse_place(place):
            """Get the location, lat, lng from a single json place."""
            location = place.get('formatted_address')
            latitude = place['location']['lat']
            longitude = place['location']['lng']
            return Location(location, (latitude, longitude), place)

        if exactly_one:
            return parse_place(places[0])
        else:
            return [parse_place(place) for place in places]

    def _geocoder_exception_handler(self, error):
        """Custom exception handling for invalid queries and exceeded quotas.

        Geocod.io returns a ``422`` status code for invalid queries, which is not mapped
        in :const:`~geopy.geocoders.base.ERROR_CODE_MAP`. The service also returns a
        ``403`` status code for exceeded quotas instead of the ``429`` code mapped in
        :const:`~geopy.geocoders.base.ERROR_CODE_MAP`
        """
        if error.status_code == 422:
            error_message = self._get_error_message(error)
            raise GeocoderQueryError(error_message)
        if error.status_code == 403:
            error_message = self._get_error_message(error)
            quota_exceeded_snippet = "You can't make this request as it is " \
                                     "above your daily maximum."
            if quota_exceeded_snippet in error_message:
                raise GeocoderQuotaExceeded(error_message)

    @staticmethod
    def _get_error_message(error):
        """Try to extract an error message from the 'error' property of a JSON response.
        """
        try:
            error_message = json.loads(error.text).get('error')
        except json.JSONDecodeError:
            error_message = None
        return error_message or 'There was an unknown issue with the query.'
