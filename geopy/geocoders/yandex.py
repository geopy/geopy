import warnings

from geopy.compat import urlencode
from geopy.exc import GeocoderParseError, GeocoderServiceError
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("Yandex", )


class Yandex(Geocoder):
    """Yandex geocoder.

    Documentation at:
        https://tech.yandex.com/maps/doc/geocoder/desc/concepts/input_params-docpage/

    .. versionadded:: 1.5.0
    """

    def __init__(
            self,
            api_key=None,
            lang=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            scheme=None,
            format_string=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """

        .. versionchanged:: 1.14.0
           Default scheme has been changed from ``http`` to ``https``.

        :param str api_key: Yandex API key (not obligatory)
            http://api.yandex.ru/maps/form.xml

        :param str lang: response locale, the following locales are
            supported: ``"ru_RU"`` (default), ``"uk_UA"``, ``"be_BY"``,
            ``"en_US"``, ``"tr_TR"``.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str user_agent:
            See :attr:`geopy.geocoders.options.default_user_agent`.

            .. versionadded:: 1.12.0

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`.

            .. versionadded:: 1.14.0

        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

            .. versionadded:: 1.14.0

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.

            .. versionadded:: 1.14.0
        """
        super(Yandex, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )
        self.api_key = api_key
        self.lang = lang
        self.api = '%s://geocode-maps.yandex.ru/1.x/' % self.scheme

    def geocode(self, query, exactly_one=True, timeout=DEFAULT_SENTINEL):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = {
            'geocode': self.format_string % query,
            'format': 'json'
        }
        if self.api_key:
            params['apikey'] = self.api_key
        if self.lang:
            params['lang'] = self.lang
        if exactly_one:
            params['results'] = 1
        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one,
        )

    def reverse(
            self,
            query,
            exactly_one=DEFAULT_SENTINEL,
            timeout=DEFAULT_SENTINEL,
            kind=None,
    ):
        """
        Return an address by location point.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param bool exactly_one: Return one result or a list of results, if
            available.

            .. versionchanged:: 1.14.0
               Default value for ``exactly_one`` was ``False``, which differs
               from the conventional default across geopy. Please always pass
               this argument explicitly, otherwise you would get a warning.
               In geopy 2.0 the default value will become ``True``.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param str kind: Type of toponym. Allowed values: `house`, `street`, `metro`,
            `district`, `locality`.

            .. versionadded:: 1.14.0

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        if exactly_one is DEFAULT_SENTINEL:
            warnings.warn('%s.reverse: default value for `exactly_one` '
                          'argument will become True in geopy 2.0. '
                          'Specify `exactly_one=False` as the argument '
                          'explicitly to get rid of this warning.' % type(self).__name__,
                          DeprecationWarning)
            exactly_one = False

        try:
            lat, lng = [
                x.strip() for x in
                self._coerce_point_to_string(query).split(',')
            ]
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")
        params = {
            'geocode': '{0},{1}'.format(lng, lat),
            'format': 'json'
        }
        if self.api_key:
            params['apikey'] = self.api_key
        if self.lang:
            params['lang'] = self.lang
        if kind:
            params['kind'] = kind
        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one
        )

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

            longitude, latitude = [
                float(_) for _ in place['Point']['pos'].split(' ')
            ]

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
