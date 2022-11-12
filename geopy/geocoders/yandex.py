from functools import partial
from urllib.parse import urlencode

from geopy.exc import GeocoderParseError, GeocoderServiceError
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("Yandex", )


class Yandex(Geocoder):
    """Yandex geocoder.

    Documentation at:
        https://tech.yandex.com/maps/doc/geocoder/desc/concepts/input_params-docpage/
    """

    api_path = '/1.x/'

    def __init__(
            self,
            api_key,
            *,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            scheme=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """

        :param str api_key: Yandex API key, mandatory.
            The key can be created at https://developer.tech.yandex.ru/

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
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )
        self.api_key = api_key
        domain = 'geocode-maps.yandex.ru'
        self.api = '%s://%s%s' % (self.scheme, domain, self.api_path)

    def geocode(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            lang=None
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param str lang: Language of the response and regional settings
            of the map. List of supported values:

            - ``tr_TR`` -- Turkish (only for maps of Turkey);
            - ``en_RU`` -- response in English, Russian map features;
            - ``en_US`` -- response in English, American map features;
            - ``ru_RU`` -- Russian (default);
            - ``uk_UA`` -- Ukrainian;
            - ``be_BY`` -- Belarusian.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = {
            'geocode': query,
            'format': 'json'
        }
        params['apikey'] = self.api_key
        if lang:
            params['lang'] = lang
        if exactly_one:
            params['results'] = 1
        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(
            self,
            query,
            *,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            kind=None,
            lang=None
    ):
        """
        Return an address by location point.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param str kind: Type of toponym. Allowed values: `house`, `street`, `metro`,
            `district`, `locality`.

        :param str lang: Language of the response and regional settings
            of the map. List of supported values:

            - ``tr_TR`` -- Turkish (only for maps of Turkey);
            - ``en_RU`` -- response in English, Russian map features;
            - ``en_US`` -- response in English, American map features;
            - ``ru_RU`` -- Russian (default);
            - ``uk_UA`` -- Ukrainian;
            - ``be_BY`` -- Belarusian.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """

        try:
            point = self._coerce_point_to_string(query, "%(lon)s,%(lat)s")
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")
        params = {
            'geocode': point,
            'format': 'json'
        }
        params['apikey'] = self.api_key
        if lang:
            params['lang'] = lang
        if kind:
            params['kind'] = kind
        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_json(self, doc, exactly_one):
        """
        Parse JSON response body.
        """
        if doc.get('error'):
            raise GeocoderServiceError(doc['error']['message'])

        try:
            places = doc['response']['GeoObjectCollection']['featureMember']
        except KeyError:
            raise GeocoderParseError('Failed to parse server response')

        def parse_code(place):
            """
            Parse each record.
            """
            try:
                place = place['GeoObject']
            except KeyError:
                raise GeocoderParseError('Failed to parse server response')

            longitude, latitude = (
                float(_) for _ in place['Point']['pos'].split(' ')
            )

            name_elements = ['name', 'description']
            location = ', '.join([place[k] for k in name_elements if place.get(k)])

            return Location(location, (latitude, longitude), place)

        if exactly_one:
            try:
                return parse_code(places[0])
            except IndexError:
                return None
        else:
            return [parse_code(place) for place in places]
