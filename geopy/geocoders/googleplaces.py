"""
:class:`.GooglePlaces` is the Google Places API.
"""
import base64
import hashlib
import hmac
from geopy.compat import urlencode
from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT, DEFAULT_SCHEME
from geopy.exc import (
    GeocoderQuotaExceeded,
    ConfigurationError,
    GeocoderQueryError,
)
from geopy.location import Location


__all__ = ("GooglePlaces", )


class GooglePlaces(Geocoder):  # pylint: disable=R0902
    """
    Geocoder using the Google Places API. Documentation at:
        https://developers.google.com/places/documentation/
    """

    def __init__(
            self,
            api_key=None,
            scheme=DEFAULT_SCHEME,
            client_id=None,
            secret_key=None,
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
            user_agent=None,
            channel=''
    ):  # pylint: disable=R0913

        """
        Initialize a customized Google geocoder.

        API authentication is only required for Google Maps Premier customers.

        :param string api_key: The API key required by Google to perform
            geocoding requests. API keys are managed through the Google APIs
            console (https://code.google.com/apis/console).

        :param string scheme: Use 'https' or 'http' as the API URL's scheme.
            Default is https. Note that SSL connections' certificates are not
            verified.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

            .. versionadded:: 1.12.1

        :param string client_id: If using premier, the account client id.

        :param string secret_key: If using premier, the account secret key.

        :param string channel: If using premier, the channel identifier.
        """
        super(GooglePlaces, self).__init__(
            scheme=scheme, timeout=timeout, proxies=proxies, user_agent=user_agent
        )
        if client_id and not secret_key:
            raise ConfigurationError('Must provide secret_key with client_id.')
        if secret_key and not client_id:
            raise ConfigurationError('Must provide client_id with secret_key.')

        self.premier = bool(client_id and secret_key)
        self.client_id = client_id
        self.secret_key = secret_key
        self.channel = channel

        self.api_key = api_key
        self.domain = 'maps.googleapis.com'

        self.autocomplete_api = '{scheme}://{domain}/maps/api/place/autocomplete/json'.format(scheme=self.scheme, domain=self.domain)
        self.details_api = '{scheme}://{domain}/maps/api/place/details/json'.format(scheme=self.scheme, domain=self.domain)


    def _get_signed_url(self, endpoint, params):
        """
        Returns a Premier account signed url. Docs on signature:
            https://developers.google.com/maps/documentation/business/webservices/auth#digital_signatures
        """
        params['client'] = self.client_id

        if self.channel:
            params['channel'] = self.channel

        path = "{}?{}".format(endpoint, urlencode(params))
        signature = hmac.new(
            base64.urlsafe_b64decode(self.secret_key),
            path.encode('utf-8'),
            hashlib.sha1
        )
        signature = base64.urlsafe_b64encode(signature.digest()).decode('utf-8')
        return '{}://{}{}&signature={}'.format(self.scheme, self.domain, path, signature)


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

    def geocode(self,
                query,
                exactly_one=False,
                timeout=None,
                location=None,
                radius=None,
                language=None,
                types=None,
                components=None,
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

        :type location: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param int radius:  The distance (in meters) within which to return place results.
            Setting a radius biases results to the indicated area, but may not fully restrict results to the specified area.

        :param string language: The language in which to return results. List of supported languages: https://developers.google.com/maps/faq#languagesupport

        :param string types: The types of place results to return.
            Possible values are "geocode", "address", "establishment", "(regions)" or "(cities)"
            If no type is specified, all types will be returned.

        :param dict components: A grouping of places to which you would like to restrict your results.
            Currently, you can use components to filter by country.
            For example: components=country:fr would restrict your results to places within France.
        """
        autocomplete_predictions = self.autocomplete(query, timeout, location, radius, language, types, components)

        if len(autocomplete_predictions) > 1 and exactly_one:
            return self.place_details(autocomplete_predictions[0].get('place_id'), language)
        else:
            return [self.place_details(place.get('place_id'), language) for place in autocomplete_predictions]

    def parse_details(self, details_page):
        status = details_page.get('status')
        if status != "OK":
            self._check_status(status)
            return None
        return details_page.get('result')

    # for getting only details about a specific place
    def place_details(self, placeid, language):
        detail_params = {}
        detail_params['key'] = self.api_key
        if not placeid:
            return []
        detail_params['placeid'] = placeid
        if language:
            detail_params['language'] = language

        if self.premier is False:
            details_url = "{}?{}".format(self.details_api, urlencode(detail_params))
        else:
            details_url = self._get_signed_url('/maps/api/details/json', detail_params)

        detail_result = self.parse_details(self._call_geocoder(details_url))
        formatted_address = detail_result['formatted_address']
        latitude = detail_result['geometry']['location']['lat']
        longitude = detail_result['geometry']['location']['lng']
        return Location(formatted_address, (latitude, longitude), detail_result)

    # for getting only autocomplete endpoint results
    def autocomplete(self,
                     query,
                     timeout=None,
                     offset=None,
                     location=None,
                     radius=None,
                     language=None,
                     types=None,
                     components=None):

        autocomplete_params = {
            'input': self.format_string % query,
        }

        if self.api_key:
            autocomplete_params['key'] = self.api_key

        if offset is not None:
            autocomplete_params['offset'] = offset

        if location is not None:
            autocomplete_params['location'] = location

        if radius is not None:
            autocomplete_params['radius'] = radius

        if language is not None:
            autocomplete_params['language'] = language

        if types is not None:
            autocomplete_params['types'] = types

        if components is not None:
            autocomplete_params['components'] = self._format_components_param(components)

        if self.premier is False:
            autocomplete_url = "{}?{}".format(self.autocomplete_api, urlencode(autocomplete_params))
        else:
            autocomplete_url = self._get_signed_url('/maps/api/autocomplete/json', autocomplete_params)

        return self.parse_autocomplete(self._call_geocoder(autocomplete_url, timeout=timeout))

    def parse_autocomplete(self, autocomplete_page):
        predictions = autocomplete_page.get('predictions', [])
        if not len(predictions):
            self._check_status(autocomplete_page.get('status'))
        return predictions

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
