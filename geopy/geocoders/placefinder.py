# *****************************************************************************
# geopy/geocoders/placefinder.py
# *****************************************************************************

from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import json
try:
    import oauth2
except ImportError:
    oauth2 = None
import time
import urllib
import urllib2

from geopy.geocoders.base import Geocoder, GeocoderError, GeocoderResultError


# *****************************************************************************
# YahooPlaceFinder
# *****************************************************************************

class YahooPlaceFinder(Geocoder):

    """
    a Geocoder that utilizes the Yahoo! BOSS PlaceFinder API

    """

    def __init__(self, consumer_key, consumer_secret):

        """
        sets consumer key and secret

        """
        if oauth2 is None:
            raise ImportError(u'No module named oauth2')

        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

    def _build_request(self, string, reverse):

        """
        returns a signed oauth request for the given query

        """

        request = oauth2.Request(
            method='GET',
            parameters={
                'oauth_nonce': oauth2.generate_nonce(),
                'oauth_timestamp': int(time.time()),
                'oauth_version': '1.0',
            },
            url='%s?location=%s&flags=J%s' % (
                'http://yboss.yahooapis.com/geo/placefinder',
                urllib.quote(string.encode('utf-8')),
                '&gflags=R' if reverse else '',
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
        returns only the results that meet the minimum quality threshold
        and are located in expected countries

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
        returns the result of a PlaceFinder API call

        """

        try:
            urllib_req = urllib2.Request(
                request.url,
                None,
                request.to_header(realm='yahooapis.com'))
            conn = urllib2.urlopen(urllib_req)
            content = conn.read()
        except urllib2.URLError:
            conn, content = None, None

        if not conn or conn.getcode() != 200:
            raise GeocoderError(
                'PlaceFinder service returned status code %s.' % (
                    conn.getcode() if conn else None,
                )
            )

        return content

    def _parse_response(self, response):

        """
        returns the parsed result of a PlaceFinder API call

        """

        try:
            placefinder = json.loads(response)['bossresponse']['placefinder']
            results = [
                (place, (float(place['latitude']), float(place['longitude'])))
                for place in placefinder.get('results', [])
            ]
        except (KeyError, ValueError):
            raise GeocoderError('Error parsing PlaceFinder result')

        return results

    @staticmethod
    def humanize(location):

        """
        returns a human readable representation of a raw PlaceFinder location

        """

        return ', '.join([
            location[line]
            for line in ['line1', 'line2', 'line3', 'line4']
            if location[line]
        ])

    def geocode(self, location, min_quality=0,
                raw=False, reverse=False, valid_country_codes=None):

        """
        returns a geocoded location using Yahoo's PlaceFinder API

        """

        request = self._build_request(location, reverse=reverse)
        response = self._get_response(request)
        results = self._parse_response(response)

        results = self._filtered_results(
            results,
            min_quality,
            valid_country_codes,
        )

        if not results:
            raise GeocoderResultError('Geocoder returned no results!')

        if not raw:
            results = [
                (YahooPlaceFinder.humanize(place), point)
                for (place, point) in results
            ]

        return results

    def reverse(self, point):

        """
        returns a reverse geocoded location using Yahoo's PlaceFinder API

        """

        try:
            point = (point.lat, point.lon)
        except AttributeError:
            pass

        try:
            point = (point.latitude, point.longitude)
        except AttributeError:
            pass

        if not isinstance(point, tuple):
            raise TypeError('point is not a tuple or a Point instance')

        return self.geocode('%s, %s' % point, reverse=True)
