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

    .. attention::
        Since September 2019 Yandex requires each request to have an API key.
        API keys can be created at https://developer.tech.yandex.ru/
    """

    api_path = '/1.x/'

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

        :param str api_key: Yandex API key, mandatory.
            The key can be created at https://developer.tech.yandex.ru/

            .. versionchanged:: 1.21.0
                API key is mandatory since September 2019.

        :param str lang: Language of the response and regional settings
            of the map. List of supported values:

            - ``tr_TR`` -- Turkish (only for maps of Turkey);
            - ``en_RU`` -- response in English, Russian map features;
            - ``en_US`` -- response in English, American map features;
            - ``ru_RU`` -- Russian (default);
            - ``uk_UA`` -- Ukrainian;
            - ``be_BY`` -- Belarusian.

            .. deprecated:: 1.22.0
                This argument will be removed in geopy 2.0.
                Use `geocode`'s and `reverse`'s `lang` instead.

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

            .. deprecated:: 1.22.0

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
        if not api_key:
            warnings.warn(
                'Since September 2019 Yandex requires each request to have an API key. '
                'Pass a valid `api_key` to Yandex geocoder to hide this warning. '
                'API keys can be created at https://developer.tech.yandex.ru/',
                UserWarning,
                stacklevel=2
            )
        self.api_key = api_key
        if lang is not None:
            warnings.warn(
                '`lang` argument of the %(cls)s.__init__ '
                'is deprecated and will be removed in geopy 2.0. Use '
                '%(cls)s.geocode(lang=%(value)r) and '
                '%(cls)s.reverse(lang=%(value)r) instead.'
                % dict(cls=type(self).__name__, value=lang),
                DeprecationWarning,
                stacklevel=2
            )
        self.lang = lang
        domain = 'geocode-maps.yandex.ru'
        self.api = '%s://%s%s' % (self.scheme, domain, self.api_path)

    def geocode(
            self,
            query,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            lang=None,
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

            .. versionadded:: 1.22.0

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        params = {
            'geocode': self.format_string % query,
            'format': 'json'
        }
        if self.api_key:
            params['apikey'] = self.api_key
        if lang is None:
            lang = self.lang
        if lang:
            params['lang'] = lang
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
            lang=None,
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

        :param str lang: Language of the response and regional settings
            of the map. List of supported values:

            - ``tr_TR`` -- Turkish (only for maps of Turkey);
            - ``en_RU`` -- response in English, Russian map features;
            - ``en_US`` -- response in English, American map features;
            - ``ru_RU`` -- Russian (default);
            - ``uk_UA`` -- Ukrainian;
            - ``be_BY`` -- Belarusian.

            .. versionadded:: 1.22.0

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """
        if exactly_one is DEFAULT_SENTINEL:
            warnings.warn('%s.reverse: default value for `exactly_one` '
                          'argument will become True in geopy 2.0. '
                          'Specify `exactly_one=False` as the argument '
                          'explicitly to get rid of this warning.' % type(self).__name__,
                          DeprecationWarning, stacklevel=2)
            exactly_one = False

        try:
            point = self._coerce_point_to_string(query, "%(lon)s,%(lat)s")
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")
        params = {
            'geocode': point,
            'format': 'json'
        }
        if self.api_key:
            params['apikey'] = self.api_key
        if lang is None:
            lang = self.lang
        if lang:
            params['lang'] = lang
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
