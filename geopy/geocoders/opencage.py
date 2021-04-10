from functools import partial
from urllib.parse import urlencode

from geopy.exc import GeocoderServiceError
from geopy.geocoders.base import DEFAULT_SENTINEL, ERROR_CODE_MAP, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("OpenCage", )


class OpenCage(Geocoder):
    """Geocoder using the OpenCageData API.

    Documentation at:
        https://opencagedata.com/api

    .. versionchanged:: 2.2
        Improved error handling by using the default errors map
        (e.g. to raise :class:`.exc.GeocoderQuotaExceeded` instead of
        :class:`.exc.GeocoderQueryError` for HTTP 402 error)
    """

    api_path = '/geocode/v1/json'

    def __init__(
            self,
            api_key,
            *,
            domain='api.opencagedata.com',
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
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
        self.domain = domain.strip('/')
        self.api = '%s://%s%s' % (self.scheme, self.domain, self.api_path)

    def geocode(
            self,
            query,
            *,
            bounds=None,
            country=None,
            language=None,
            annotations=True,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

        :type bounds: list or tuple of 2 items of :class:`geopy.point.Point` or
            ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.
        :param bounds: Provides the geocoder with a hint to the region
            that the query resides in. This value will help the geocoder
            but will not restrict the possible results to the supplied
            region. The bounds parameter should be specified as 2
            coordinate points -- corners of a bounding box.
            Example: ``[Point(22, 180), Point(-22, -180)]``.

        :param country: Restricts the results to the specified
            country or countries. The country code is a 2 character code as
            defined by the ISO 3166-1 Alpha 2 standard (e.g. ``fr``).
            Might be a Python list of strings.
        :type country: str or list

        :param str language: an IETF format language code (such as `es`
            for Spanish or pt-BR for Brazilian Portuguese); if this is
            omitted a code of `en` (English) will be assumed by the remote
            service.

        :param bool annotations: Enable
            `annotations <https://opencagedata.com/api#annotations>`_
            data, which can be accessed via :attr:`.Location.raw`.
            Set to False if you don't need it to gain a little performance
            win.

            .. versionadded:: 2.2

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
            'q': query,
        }
        if not annotations:
            params['no_annotations'] = 1
        if bounds:
            params['bounds'] = self._format_bounding_box(
                bounds, "%(lon1)s,%(lat1)s,%(lon2)s,%(lat2)s")
        if language:
            params['language'] = language

        if not country:
            country = []
        if isinstance(country, str):
            country = [country]
        if country:
            params['countrycode'] = ",".join(country)

        url = "?".join((self.api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(
            self,
            query,
            *,
            language=None,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
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

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """

        params = {
            'key': self.api_key,
            'q': self._coerce_point_to_string(query),
        }
        if language:
            params['language'] = language

        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

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

    def _check_status(self, status):
        status_code = status['code']
        message = status['message']
        if status_code == 200:
            return
        # https://opencagedata.com/api#codes
        exc_cls = ERROR_CODE_MAP.get(status_code, GeocoderServiceError)
        raise exc_cls(message)
