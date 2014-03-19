"""
:class:`.YahooPlaceFinder` geocoder.
support.
"""

import json

try:
    import requests
    import requests_oauthlib
    requests_missing = False
except ImportError:
    requests_missing = True

from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT
from geopy.exc import GeocoderParseError
from geopy.location import Location
from geopy.compat import quote


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
        if requests_missing:
            raise ImportError(
                'requests-oauthlib is needed for YahooPlaceFinder'
            )
        super(YahooPlaceFinder, self).__init__(timeout=timeout, proxies=proxies)
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api = 'https://yboss.yahooapis.com/geo/placefinder'

    def _call_yahoo(self, query, reverse, exactly_one, timeout):
        """
        Returns a response for the given query
        """
        # we quote the location, because spaces must be encoded as "%20"
        # instead of "+". this also means we can't later call urlencode on
        # this value.
        params = {'location': quote(query), 'flags': 'J'}

        if reverse is True:
            params['gflags'] = 'R'
        if exactly_one is True:
            params['count'] = '1'

        auth = requests_oauthlib.OAuth1(
            self.consumer_key, self.consumer_secret)

        url = u'?'.join((
            self.api,
            u'&'.join(u'='.join(item) for item in params.items())
        ))

        return requests.get(url, auth=auth, timeout=timeout)

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
            placefinder = json.loads(response.content)['bossresponse']['placefinder']
            if not len(placefinder) or not len(placefinder.get('results', [])):
                return None
            results = [
                Location(
                    place['name'],
                    (float(place['latitude']), float(place['longitude'])),
                    place
                )
                for place in placefinder['results']
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
