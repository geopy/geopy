import warnings

from geopy.compat import string_compare, urlencode
from geopy.exc import GeocoderQueryError, GeocoderQuotaExceeded
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("OpenCage", )


class OpenCage(Geocoder):
    """Geocoder using the OpenCageData API.

    Documentation at:
        https://opencagedata.com/api

    .. versionadded:: 1.1.0
    """

    api_path = '/geocode/v1/json'

    def __init__(
            self,
            api_key,
            domain='api.opencagedata.com',
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            format_string=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """

        :param str api_key: The API key required by OpenCageData
            to perform geocoding requests. You can get your key here:
            https://opencagedata.com/

        :param str domain: Currently it is ``'api.opencagedata.com'``, can
            be changed for testing purposes.

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str user_agent:
            See :attr:`geopy.geocoders.options.default_user_agent`.

            .. versionadded:: 1.12.0

        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

            .. versionadded:: 1.14.0

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.

            .. versionadded:: 1.14.0

        """
        super(OpenCage, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
        )

        self.api_key = api_key
        self.domain = domain.strip('/')
        self.api = '%s://%s%s' % (self.scheme, self.domain, self.api_path)

    def geocode(
            self,
            query,
            bounds=None,
            country=None,
            language=None,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

        :param str language: an IETF format language code (such as `es`
            for Spanish or pt-BR for Brazilian Portuguese); if this is
            omitted a code of `en` (English) will be assumed by the remote
            service.

        :type bounds: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.
        :param bounds: Provides the geocoder with a hint to the region
            that the query resides in. This value will help the geocoder
            but will not restrict the possible results to the supplied
            region. The bounds parameter should be specified as 2
            coordinate points -- corners of a bounding box.
            Example: ``[Point(22, 180), Point(-22, -180)]``.

            .. versionchanged:: 1.17.0
                Previously the only supported format for bounds was a
                string of ``"longitude,latitude,longitude,latitude"``.
                This format is now deprecated in favor of a list/tuple
                of a pair of geopy Points and will be removed in geopy 2.0.

        :param str country: Provides the geocoder with a hint to the
            country that the query resides in. This value will help the
            geocoder but will not restrict the possible results to the
            supplied country. The country code is a 3 character code as
            defined by the ISO 3166-1 Alpha 3 standard.

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
            'key': self.api_key,
            'q': self.format_string % query,
        }
        if bounds:
            if isinstance(bounds, string_compare):
                warnings.warn(
                    'OpenCage `bounds` format of '
                    '`"longitude,latitude,longitude,latitude"` is now '
                    'deprecated and will be not supported in geopy 2.0. '
                    'Use `[Point(latitude, longitude), Point(latitude, longitude)]` '
                    'instead.',
                    UserWarning
                )
                lon1, lat1, lon2, lat2 = bounds.split(',')
                bounds = [[lat1, lon1], [lat2, lon2]]
            params['bounds'] = self._format_bounding_box(
                bounds, "%(lon1)s,%(lat1)s,%(lon2)s,%(lat2)s")
        if language:
            params['language'] = language
        if country:
            params['country'] = country

        url = "?".join((self.api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    def reverse(
            self,
            query,
            language=None,
            exactly_one=DEFAULT_SENTINEL,
            timeout=DEFAULT_SENTINEL,
    ):
        """
        Return an address by location point.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param str language: The language in which to return results.

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

        params = {
            'key': self.api_key,
            'q': self._coerce_point_to_string(query),
        }
        if language:
            params['language'] = language

        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    def _parse_json(self, page, exactly_one=True):
        '''Returns location, (latitude, longitude) from json feed.'''

        places = page.get('results', [])
        if not len(places):
            self._check_status(page.get('status'))
            return None

        def parse_place(place):
            '''Get the location, lat, lng from a single json place.'''
            location = place.get('formatted')
            latitude = place['geometry']['lat']
            longitude = place['geometry']['lng']
            return Location(location, (latitude, longitude), place)

        if exactly_one:
            return parse_place(places[0])
        else:
            return [parse_place(place) for place in places]

    @staticmethod
    def _check_status(status):
        """
        Validates error statuses.
        """
        status_code = status['code']
        if status_code == 429:
            # Rate limit exceeded
            raise GeocoderQuotaExceeded(
                'The given key has gone over the requests limit in the 24'
                ' hour period or has submitted too many requests in too'
                ' short a period of time.'
            )
        if status_code == 200:
            # When there are no results, just return.
            return

        if status_code == 403:
            raise GeocoderQueryError(
                'Your request was denied.'
            )
        else:
            raise GeocoderQueryError('Unknown error.')
