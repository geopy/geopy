"""
:class:`.GooglePlaces` is the Google Places API.
"""

import base64
import hashlib
import hmac
from geopy.compat import urlencode
from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT, DEFAULT_SCHEME
from geopy.exc import (
    GeocoderQueryError,
    GeocoderQuotaExceeded,
    ConfigurationError,
    GeocoderParseError,
    GeocoderQueryError,
)
from geopy.location import Location
from geopy.util import logger

try:
    from pytz import timezone, UnknownTimeZoneError
    from calendar import timegm
    from datetime import datetime
    from numbers import Number
    pytz_available = True
except ImportError:
    pytz_available = False


__all__ = ("GooglePlaces", )


class GooglePlaces(Geocoder):  # pylint: disable=R0902
    """
    Geocoder using the Google Places API. Documentation at:
        https://developers.google.com/places/documentation/
    """

    def __init__(
            self,
            api_key=None,
            domain='maps.googleapis.com',
            scheme=DEFAULT_SCHEME,
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
            user_agent=None,
        ):  # pylint: disable=R0913
        """
        Initialize a customized Google geocoder.

        API authentication is only required for Google Maps Premier customers.

        :param string api_key: The API key required by Google to perform
            geocoding requests. API keys are managed through the Google APIs
            console (https://code.google.com/apis/console).

        :param string domain: Should be the localized Google Maps domain to
            connect to. The default is 'maps.googleapis.com', but if you're
            geocoding address in the UK (for example), you may want to set it
            to 'maps.google.co.uk' to properly bias results.

        :param string scheme: Use 'https' or 'http' as the API URL's scheme.
            Default is https. Note that SSL connections' certificates are not
            verified.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.
        """
        super(GooglePlaces, self).__init__(
            scheme=scheme, timeout=timeout, proxies=proxies, user_agent=user_agent
        )

        self.api_key = api_key
        self.domain = domain.strip('/')
        self.scheme = scheme
        self.doc = {}


        self.autocomplete_api = '%s://%s/maps/api/place/autocomplete/json' % (self.scheme, self.domain)
        self.details_api = '%s://%s/maps/api/place/details/json' % (self.scheme, self.domain)


    @staticmethod
    def _format_components_param(components):
        """
        Format the components dict to something Google understands.
        """
        return "|".join(
            (":".join(item)
             for item in components.items()
            )
        )

    def geocode(
            self,
            query,
            exactly_one=False,
            timeout=None,
            offset = None,
            location = None,
            radius = None,
            language = None,
            types = None,
            components = None,
        ):  # pylint: disable=W0221,R0913
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

            .. versionadded:: 1.12

        :param offset: The position, in the input term, of the last character that the service uses to match predictions.
            For example, if the input is 'Google' and the offset is 3, the service will match on 'Goo'.
            If no offset is supplied, the service will use the whole term.
        :type offset: int

        :type location: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param int radius:  The distance (in meters) within which to return place results.
            Setting a radius biases results to the indicated area, but may not fully restrict results to the specified area.

        :param string language: The language in which to return results.

        :param string types: The types of place results to return.
            Possible values are "geocode", "address", "establishment", "(regions)" or "(cities)"
            If no type is specified, all types will be returned.

        :param dict components: A grouping of places to which you would like to restrict your results.
            Currently, you can use components to filter by country.
            For example: components=country:fr would restrict your results to places within France.
        """
        autocomplete_params = {
            'input': self.format_string % query,
        }
        detail_params = {}
        if self.api_key:
            autocomplete_params['key'] = self.api_key
            detail_params['key'] = self.api_key

        if offset:
            autocomplete_params['offset'] = offset

        if location:
            autocomplete_params['location'] = location

        if radius:
            autocomplete_params['radius'] = radius

        if language:
            autocomplete_params['language'] = language
            detail_params['language'] = language

        if types:
            autocomplete_params['types'] = types

        if components:
            autocomplete_params['components'] = self._format_components_param(components)

        autocomplete_url = "?".join((self.autocomplete_api, urlencode(autocomplete_params)))
        logger.debug("%s.google_places_autocomplete: %s", self.__class__.__name__, autocomplete_url)
        autocomplete_predictions = self.parse_autocomplete(self._call_geocoder(autocomplete_url, timeout=timeout))

        return [self.parse_predictions(place,detail_params) for place in autocomplete_predictions]


    def parse_autocomplete(self, autocomplete_page):
        predictions = autocomplete_page.get('predictions', [])
        if not len(predictions):
            self._check_status(autocomplete_page.get('status'))
            return None
        return predictions


    def parse_details(self, details_page):
        status = details_page.get('status')
        if status != "OK":
            self._check_status(status)
            return None
        return details_page.get('result')


    # uses the seconds api call to "details" to fetch lat lon info on a place to build the Location object
    def parse_predictions(self, place, detail_params):
        detail_params['placeid'] = place.get('place_id')
        details_url = "?".join((self.details_api, urlencode(detail_params)))
        logger.debug("%s.google_places_details: %s", self.__class__.__name__, details_url)
        detail_result =self.parse_details(self._call_geocoder(details_url))
        formatted_address = detail_result['formatted_address']
        latitude = detail_result['geometry']['location']['lat']
        longitude = detail_result['geometry']['location']['lng']
        return Location(formatted_address, (latitude, longitude), detail_result)


    @staticmethod
    def _check_status(status):
        """
        Validates error statuses.
        """
        if status == 'ZERO_RESULTS':
            # When there are no results, just return.
            return
        if status == 'OVER_QUERY_LIMIT':
            raise GeocoderQuotaExceeded(
                'The given key has gone over the requests limit in the 24'
                ' hour period or has submitted too many requests in too'
                ' short a period of time.'
            )
        elif status == 'REQUEST_DENIED':
            raise GeocoderQueryError(
                'Your request was denied.'
            )
        elif status == 'INVALID_REQUEST':
            raise GeocoderQueryError('Probably missing address or latlng.')
        else:
            raise GeocoderQueryError('Unknown error.')

