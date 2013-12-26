"""
:class:`.YahooPlaceFinder` geocoder.
support.
"""

import json

from geopy.compat import Request, urlencode
from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT
from geopy.exc import GeocoderParseError

try:
    import oauthlib # pylint: disable=F0401
except ImportError:
    oauthlib = None


class YahooPlaceFinder(Geocoder): # pylint: disable=W0223
    """
    Geocoder that utilizes the Yahoo! BOSS PlaceFinder API. Documentation at:
        https://developer.yahoo.com/boss/geo/docs/
    """

    def __init__(self, consumer_key, consumer_secret, # pylint: disable=R0913
                        timeout=DEFAULT_TIMEOUT, proxies=None):
        """
        :param string consumer_key: Key provided by Yahoo.

        :param string consumer_secret: Secret corresponding to the key
            provided by Yahoo.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

            .. versionadded:: 0.96
        """
        if oauthlib is None:
            raise ImportError('oauthlib package is needed for YahooPlaceFinder')
        super(YahooPlaceFinder, self).__init__(timeout=timeout, proxies=proxies)
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api = 'https://yboss.yahooapis.com/geo/placefinder'

    def _call_yahoo(self, query, reverse, exactly_one, timeout):
        """
        Returns a signed oauth request for the given query
        """
        params = {'location': query, 'flags': 'J'}
        if reverse is True:
            params['gflags'] = 'R'
        if exactly_one is True:
            params['count'] = 1

        client = oauthlib.oauth1.Client(
            self.consumer_key,
            self.consumer_secret,
            signature_method="HMAC-SHA1"
        )
        url, headers, body = client.sign(
            "?".join((self.api, urlencode(params))), realm='yahooapis.com'
        )
        request = Request(url, body, headers)

        return self._call_geocoder(
            request, timeout=timeout, raw=True
        )

    @staticmethod
    def _filtered_results(results, min_quality, valid_country_codes):
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

    @staticmethod
    def _parse_response(response):
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

    def geocode(self, query, exactly_one=True, timeout=None, # pylint: disable=W0221,R0913
                        min_quality=0, raw=False,
                        reverse=False, valid_country_codes=None):
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int min_quality:

        :param bool raw:

        :param bool reverse:

        :param valid_country_codes:
        :type valid_country_codes: list or tuple
        """
        response = self._call_yahoo(query, reverse, exactly_one, timeout)
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
                (self.humanize(place), point)
                for (place, point) in results
            ]

        if exactly_one:
            return results[0]
        else:
            return results

    def reverse(self, query, exactly_one=True, timeout=None):
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
            exactly_one=exactly_one,
            timeout=timeout,
            reverse=True
        )
