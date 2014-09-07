"""
:class:`.YahooPlaceFinder` geocoder.
"""

try:
    from requests import get
    from requests_oauthlib import OAuth1
    requests_missing = False
except ImportError:
    requests_missing = True

from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT
from geopy.exc import GeocoderParseError
from geopy.location import Location
from geopy.compat import string_compare, py3k


__all__ = ("YahooPlaceFinder", )


class YahooPlaceFinder(Geocoder): # pylint: disable=W0223
    """
    Geocoder that utilizes the Yahoo! BOSS PlaceFinder API. Documentation at:
        https://developer.yahoo.com/boss/geo/docs/
    """

    def __init__(
            self,
            consumer_key,
            consumer_secret,
            timeout=DEFAULT_TIMEOUT,
            proxies=None
        ):  # pylint: disable=R0913
        """
        :param string consumer_key: Key provided by Yahoo.

        :param string consumer_secret: Secret corresponding to the key
            provided by Yahoo.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

        :param dict proxies: If specified, routes this geocoder"s requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

            .. versionadded:: 0.96
        """
        if requests_missing:
            raise ImportError(
                'requests-oauthlib is needed for YahooPlaceFinder.'
                ' Install with `pip install geopy -e ".[placefinder]"`.'
            )
        super(YahooPlaceFinder, self).__init__(
            timeout=timeout, proxies=proxies
        )
        self.consumer_key = (
            unicode(consumer_key)
            if not py3k
            else str(consumer_key)
        )
        self.consumer_secret = (
            unicode(consumer_secret)
            if not py3k
            else str(consumer_secret)
        )
        self.auth = OAuth1(
            client_key=self.consumer_key,
            client_secret=self.consumer_secret,
            signature_method=u"HMAC-SHA1",
            signature_type=u"AUTH_HEADER",
        )
        self.api = "https://yboss.yahooapis.com/geo/placefinder"

    @staticmethod
    def _filtered_results(results, min_quality, valid_country_codes):
        """
        Returns only the results that meet the minimum quality threshold
        and are located in expected countries.
        """
        if min_quality:
            results = [
                loc
                for loc in results
                if int(loc.raw["quality"]) > min_quality
            ]

        if valid_country_codes:
            results = [
                loc
                for loc in results
                if loc.raw["countrycode"] in valid_country_codes
            ]

        return results

    def _parse_response(self, content):
        """
        Returns the parsed result of a PlaceFinder API call.
        """
        try:
            placefinder = (
                content["bossresponse"]["placefinder"]
            )
            if not len(placefinder) or not len(placefinder.get("results", [])):
                return None
            results = [
                Location(
                    self.humanize(place),
                    (float(place["latitude"]), float(place["longitude"])),
                    raw=place
                )
                for place in placefinder["results"]
            ]
        except (KeyError, ValueError):
            raise GeocoderParseError("Error parsing PlaceFinder result")

        return results

    @staticmethod
    def humanize(location):
        """
        Returns a human readable representation of a raw PlaceFinder location
        """
        return ", ".join([
            location[line]
            for line in ["line1", "line2", "line3", "line4"]
            if location[line]
        ])

    def geocode(
            self,
            query,
            exactly_one=True,
            timeout=None,
            min_quality=0,
            reverse=False,
            valid_country_codes=None,
        ):  # pylint: disable=W0221,R0913
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int min_quality:

        :param bool reverse:

        :param valid_country_codes:
        :type valid_country_codes: list or tuple
        """
        params = {
            "location": query,
            "flags": "J", # JSON
        }

        if reverse is True:
            params["gflags"] = "R"
        if exactly_one is True:
            params["count"] = "1"

        response = self._call_geocoder(
            self.api,
            timeout=timeout,
            requester=get,
            params=params,
            auth=self.auth,
        )
        results = self._parse_response(response)
        if results is None:
            return None

        results = self._filtered_results(
            results,
            min_quality,
            valid_country_codes,
        )

        if exactly_one:
            return results[0]
        else:
            return results

    def reverse(self, query, exactly_one=True, timeout=None):
        """
        Returns a reverse geocoded location using Yahoo"s PlaceFinder API.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param bool exactly_one: Return one result or a list of results, if
            available.
        """
        query = self._coerce_point_to_string(query)
        if isinstance(query, string_compare):
            query = query.replace(" ", "") # oauth signature failure; todo
        return self.geocode(
            query,
            exactly_one=exactly_one,
            timeout=timeout,
            reverse=True
        )
