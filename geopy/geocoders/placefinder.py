"""
:class:`.YahooPlaceFinder` geocoder.
"""

from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

from geopy.compat import json, oauth2

import time
import urllib
import urllib2

from geopy.geocoders.base import Geocoder, GeocoderError


class YahooPlaceFinder(Geocoder):
    """
    Geocoder that utilizes the Yahoo! BOSS PlaceFinder API. Documentation at:
        http://developer.yahoo.com/boss/geo/docs/
    """

    def __init__(self, consumer_key, consumer_secret):
        """
        Sets consumer key and secret.
        """
        super(YahooPlaceFinder, self).__init__()
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
            urllib_req = urllib2.Request(
                request.url,
                None,
                request.to_header(realm='yahooapis.com'),
            )
            response = urllib2.urlopen(urllib_req)
            content = response.read()
        except urllib2.HTTPError as exc:
            raise GeocoderError(
                'PlaceFinder service returned status code %s.' % exc.code,
            )
        except urllib2.URLError as exc:
            raise GeocoderError(
                'PlaceFinder service exception %s.' % exc.reason,
            )

        return content

    def _parse_response(self, response):
        """
        Returns the parsed result of a PlaceFinder API call.
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

    def geocode(self, query, min_quality=0,
                raw=False, reverse=False, valid_country_codes=None):
        """
        Returns a geocoded location using Yahoo's PlaceFinder API.
        """
        super(YahooPlaceFinder, self).geocode(query)
        request = self._build_request(query, reverse=reverse)
        response = self._get_response(request)
        results = self._parse_response(response)

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

        return results

    def reverse(self, inp):
        """
        Returns a reverse geocoded location using Yahoo's PlaceFinder API.
        """
        # TODO cleanup
        point = None
        try:
            point = (inp.lat, inp.lon)
        except AttributeError:
            pass
        try:
            point = (inp.latitude, inp.longitude)
        except AttributeError:
            pass

        if not isinstance(point, tuple):
            raise TypeError('point is not a tuple or a Point instance')

        return self.geocode('%s, %s' % point, reverse=True)
