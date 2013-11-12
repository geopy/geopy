"""
:class:`.YahooPlaceFinder` geocoder. It needs significant refactoring to
replace oauth2 with oauthlib, use the base Geocoder template, ensure py3k
support, and add `count` param to requests for exactly_one.
"""

import json
import time

from geopy.compat import Request, quote
from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT, DEFAULT_SCHEME
from geopy.exc import GeocoderServiceError, GeocoderParseError

try:
    import oauth2 # pylint: disable=F0401
except ImportError:
    oauth2 = None


class YahooPlaceFinder(Geocoder): # pylint: disable=W0223
    """
    Geocoder that utilizes the Yahoo! BOSS PlaceFinder API. Documentation at:
        https://developer.yahoo.com/boss/geo/docs/
    """

    def __init__(self, consumer_key, consumer_secret, # pylint: disable=R0913
                        scheme=DEFAULT_SCHEME, timeout=DEFAULT_TIMEOUT,
                        proxies=None):
        """
        :param string consumer_key: Key provided by Yahoo.

        :param string consumer_secret: Secret corresponding to the key
            provided by Yahoo.

        :param string scheme: Use 'https' or 'http' as the API URL's scheme.
            Default is https. Note that SSL connections' certificates are not
            verified.

            .. versionadded:: 0.97

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

            .. versionadded:: 0.96
        """
        if oauth2 is None:
            raise ImportError('oauth2 is needed for YahooPlaceFinder')
        if Request is None:
            raise NotImplementedError("YahooPlaceFinder is not compatible with Py3k")
        super(YahooPlaceFinder, self).__init__(scheme=scheme, timeout=timeout, proxies=proxies)
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api = '%s://yboss.yahooapis.com/geo/placefinder' % self.scheme

    def _build_request(self, string, reverse):
        """
        Returns a signed oauth request for the given query
        """
        request = oauth2.Request(
            method='GET',
            parameters={
                'oauth_nonce': oauth2.generate_nonce(),
                'oauth_timestamp': int(time.time()),
                'oauth_version': '1.0',
            },
            url='%s?location=%s&flags=J%s' % (
                self.api,
                quote(string.encode('utf-8')),
                '&gflags=R' if reverse else '', # todo refactor
            ),
        )

        request.sign_request(
            oauth2.SignatureMethod_HMAC_SHA1(),
            oauth2.Consumer(self.consumer_key, self.consumer_secret),
            None,
        )

        return request

    def _filtered_results(self, results, min_quality, valid_country_codes):
        """
        Returns only the results that meet the minimum quality threshold
        and are located in expected countries.
        """
        results = [
            (place, point)
            for (place, point) in results
            if int(place['quality']) > min_quality
        ]

        if valid_country_codes:
            results = [
                (place, point)
                for (place, point) in results
                if place['countrycode'] in valid_country_codes
            ]

        return results

    def _get_response(self, request):
        """
        Returns the result of a PlaceFinder API call.
        """
        try:
            urllib_req = Request(
                request.url,
                None,
                request.to_header(realm='yahooapis.com'),
            )
            response = self.urlopen(urllib_req)
            content = response.read()
        except Exception as exc:
            raise GeocoderServiceError(str(exc))
        return content

    def _parse_response(self, response):
        """
        Returns the parsed result of a PlaceFinder API call.
        """
        try:
            placefinder = json.loads(response)['bossresponse']['placefinder']
            if not len(placefinder):
                return None
            results = [
                (place, (float(place['latitude']), float(place['longitude'])))
                for place in placefinder.get('results', [])
            ]
        except (KeyError, ValueError):
            raise GeocoderParseError('Error parsing PlaceFinder result')

        return results

    @staticmethod
    def humanize(location):
        """
        Returns a human readable representation of a raw PlaceFinder location
        """
        return ', '.join([
            location[line]
            for line in ['line1', 'line2', 'line3', 'line4']
            if location[line]
        ])

    def geocode(self, query, min_quality=0, raw=False, reverse=False, # pylint: disable=W0221,R0913
                        valid_country_codes=None, exactly_one=True):
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param int min_quality:

        :param bool raw:

        :param bool reverse:

        :param valid_country_codes:
        :type valid_country_codes: list or tuple

        :param bool exactly_one: Return one result or a list of results, if
            available.
        """
        request = self._build_request(query, reverse=reverse)
        response = self._get_response(request)
        results = self._parse_response(response)
        if results is None:
            return None

        results = self._filtered_results(
            results,
            min_quality,
            valid_country_codes,
        )

        if not raw:
            results = [
                (YahooPlaceFinder.humanize(place), point)
                for (place, point) in results
            ]

        if exactly_one:
            return results[0]
        else:
            return results

    def reverse(self, query, exactly_one=True):
        """
        Returns a reverse geocoded location using Yahoo's PlaceFinder API.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param bool exactly_one: Return one result or a list of results, if
            available.
        """
        return self.geocode(
            self._coerce_point_to_string(query),
            reverse=True,
            exactly_one=exactly_one
        )
