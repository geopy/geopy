"""
:class:`.OpenCage` is the Opencagedata geocoder.
"""

from geopy.compat import urlencode
from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT, DEFAULT_SCHEME
from geopy.exc import (
    GeocoderQueryError,
    GeocoderQuotaExceeded,
)
from geopy.location import Location
from geopy.util import logger


__all__ = ("OpenCage", )


class OpenCage(Geocoder):
    """
    Geocoder using the Open Cage Data API. Documentation at:
        http://geocoder.opencagedata.com/api.html

    ..versionadded:: 1.1.0
    """

    def __init__(
            self,
            api_key,
            domain='api.opencagedata.com',
            scheme=DEFAULT_SCHEME,
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
    ):  # pylint: disable=R0913
        """
        Initialize a customized Open Cage Data geocoder.

        :param string api_key: The API key required by Open Cage Data
            to perform geocoding requests. You can get your key here:
            https://developer.opencagedata.com/

        :param string domain: Currently it is 'api.opencagedata.com', can
            be changed for testing purposes.

        :param string scheme: Use 'https' or 'http' as the API URL's scheme.
            Default is https. Note that SSL connections' certificates are not
            verified.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

        """
        super(OpenCage, self).__init__(
            scheme=scheme, timeout=timeout, proxies=proxies
        )

        self.api_key = api_key
        self.domain = domain.strip('/')
        self.scheme = scheme
        self.api = '%s://%s/geocode/v1/json' % (self.scheme, self.domain)

    def geocode(
            self,
            query,
            bounds=None,
            country=None,
            language=None,
            exactly_one=True,
            timeout=None,
    ):  # pylint: disable=W0221,R0913
        """
        Geocode a location query.

        :param string query: The query string to be geocoded; this must
            be URL encoded.

        :param string language: an IETF format language code (such as `es`
            for Spanish or pt-BR for Brazilian Portuguese); if this is
            omitted a code of `en` (English) will be assumed by the remote
            service.

        :param string bounds: Provides the geocoder with a hint to the region
            that the query resides in. This value will help the geocoder
            but will not restrict the possible results to the supplied
            region. The bounds parameter should be specified as 4
            coordinate points forming the south-west and north-east
            corners of a bounding box. For example,
            `bounds=-0.563160,51.280430,0.278970,51.683979`.

        :param string country: Provides the geocoder with a hint to the
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

        """
        params = {
            'key': self.api_key,
            'q': self.format_string % query,
        }
        if bounds:
            params['bounds'] = bounds
        if bounds:
            params['language'] = language
        if bounds:
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
            exactly_one=False,
            timeout=None,
    ):  # pylint: disable=W0221,R0913
        """
        Given a point, find an address.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param string language: The language in which to return results.

        :param boolean exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        """
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
