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
        adapter_factory=None
    ):
        """
        :param str api_key:
            A valid Geocod.io API key. (https://dash.geocod.io/apikey/create)

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

        :param callable adapter_factory:
            See :attr:`geopy.geocoders.options.default_adapter_factory`.
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
        street=None,
        city=None,
        state=None,
        postal_code=None,
        country=None
    ):
        """Return a location point by address. You may either provide a single address
        string as a ``query`` argument or individual address components using the
        ``street``, ``city``, ``state``, ``postal_code``, and ``country`` arguments.

        :param str query: The address or query you wish to geocode. You must either
            provide this argument or a valid combination of ``street``, ``city``,
            ``state``, and ``postal_code`` and you may not provide those arguments if
            also providing ``query``.

        :param int limit: The maximum number of matches to return. This will be reset
            to 1 if ``exactly_one`` is ``True``.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param str street: The street address to geocode. If providing this argument
            you must provide at least one of ``city``, ``state``, or ``postal_code``, and
            you must *not* provide a ``query`` argument.

        :param str city: The city of the address to geocode. If providing this argument
            you must *not* provide a ``query`` argument.

        :param str state: The state of the address to geocode. If providing this argument
            you must *not* provide a ``query`` argument.

        :param str postal_code: The postal code of the address to geocode. If providing
            this argument you must *not* provide a ``query`` argument.

        :param str country: The country of the address to geocode. If providing this
            argument you must *not* provide a ``query`` argument.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        if query is not None and \
                any(p is not None for p in (city, state, postal_code, country)):
            raise GeocoderQueryError('Address component must not be provided if '
                                     'query argument is used.')
        if street is not None and \
                not any(p is not None for p in (city, state, postal_code)):
            raise GeocoderQueryError('If street is provided must also provide city, '
                                     'state, and/or postal_code.')

        api = '%s://%s%s' % (self.scheme, self.domain, self.geocode_path)

        params = dict(
            api_key=self.api_key,
            q=query,
            street=street,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            limit=limit
        )
        params = {
            k: v for k, v in params.items() if v is not None
        }

        url = "?".join((api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(
        self,
        query,
        *,
        exactly_one=True,
        timeout=DEFAULT_SENTINEL,
        limit=None
    ):
        """Return an address by location point.

        :param str query: The coordinates for which you wish to obtain the
            closest human-readable addresses

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param int limit: The maximum number of matches to return. This will be reset
            to 1 if ``exactly_one`` is ``True``.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = {
            'q': self._coerce_point_to_string(query),
            'api_key': self.api_key
        }
        if limit is not None:
            params['limit'] = limit

        api = '%s://%s%s' % (self.scheme, self.domain, self.reverse_path)

        url = "?".join((api, urlencode(params)))

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
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
