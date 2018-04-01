"""
:class:`.What3Words` geocoder.
"""

import re
from geopy.compat import urlencode
from geopy.geocoders.base import (
    Geocoder,
    DEFAULT_FORMAT_STRING,
    DEFAULT_TIMEOUT,
    DEFAULT_SCHEME
)
from geopy.location import Location
from geopy.util import logger, join_filter
from geopy import exc


__all__ = ("What3Words", )


class What3Words(Geocoder):
    """
    What3Words geocoder, documentation at:
        http://what3words.com/api/reference
    """

    word_re = re.compile(r"^\*{1,1}[^\W\d\_]+$", re.U)
    multiple_word_re = re.compile(
        r"[^\W\d\_]+\.{1,1}[^\W\d\_]+\.{1,1}[^\W\d\_]+$", re.U
        )

    def __init__(
            self,
            api_key,
            format_string=DEFAULT_FORMAT_STRING,
            scheme=DEFAULT_SCHEME,
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
            user_agent=None,
    ):
        """
        Initialize a What3Words geocoder with 3-word or OneWord-address and
        What3Words API key.

            .. versionadded:: 1.5.0

        :param str api_key: Key provided by What3Words.

        :param str format_string: String containing '%s' where the
            string to geocode should be interpolated before querying the
            geocoder. For example: '%s, piped.gains.jungle'. The default
            is just '%s'.

        :param str scheme: Use 'https' or 'http' as the API URL's scheme.
            Default is https. Note that SSL connections' certificates are not
            verified.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

        :param str user_agent: Use a custom User-Agent header.

            .. versionadded:: 1.12.0
        """
        super(What3Words, self).__init__(
            format_string,
            scheme,
            timeout,
            proxies,
            user_agent=user_agent,
        )
        self.api_key = api_key
        self.api = (
            "%s://api.what3words.com/" % self.scheme
        )

    def _check_query(self, query):
        """
        Check query validity with regex
        """
        if not (self.word_re.match(query) or
                self.multiple_word_re.match(query)):
            return False
        else:
            return True

    def geocode(self,
                query,
                lang='en',
                exactly_one=True,
                timeout=None):

        """
        Geocode a "3 words" or "OneWord" query.

        :param str query: The 3-word or OneWord-address you wish to geocode.

        :param str lang: two character language codes as supported by
            the API (http://what3words.com/api/reference/languages).

        :param bool exactly_one: Parameter has no effect for this geocoder.
            Due to the address scheme there is always exactly one result.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.
            .. versionadded:: 0.97
        """

        if not self._check_query(query):
            raise exc.GeocoderQueryError(
                "Search string must be either like "
                "'word.word.word' or '*word' "
            )

        params = {
            'string': self.format_string % query,
            'lang': self.format_string % lang.lower(),
            'key': self.api_key,
        }

        url = "?".join(((self.api + "w3w"), urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one
        )

    def _parse_json(self, resources, exactly_one=True):
        """
        Parse type, words, latitude, and longitude and language from a
        JSON response.
        """
        if resources.get('error') == "X1":
            raise exc.GeocoderAuthenticationFailure()

        if resources.get('error') == "11":
            raise exc.GeocoderQueryError(
                "Address (Word(s)) not recognised by What3Words."
            )

        def parse_resource(resource):
            """
            Parse record.
            """

            if resource['type'] == '3 words':
                words = resource['words']
                words = join_filter(".", [words[0], words[1], words[2]])
                position = resource['position']
                latitude, longitude = position[0], position[1]

                if latitude and longitude:
                    latitude = float(latitude)
                    longitude = float(longitude)

                return Location(words, (latitude, longitude), resource)
            elif resource['type'] == 'OneWord':
                words = resource['words']
                words = join_filter(".", [words[0], words[1], words[2]])
                oneword = resource['oneword']
                info = resource['info']

                address = join_filter(", ", [
                    oneword,
                    words,
                    info['name'],
                    info['address1'],
                    info['address2'],
                    info['address3'],
                    info['city'],
                    info['county'],
                    info['postcode'],
                    info['country_id']
                ])

                position = resource['position']
                latitude, longitude = position[0], position[1]

                if latitude and longitude:
                    latitude = float(latitude)
                    longitude = float(longitude)

                return Location(address, (latitude, longitude), resource)
            else:
                raise exc.GeocoderParseError('Error parsing result.')


        return parse_resource(resources)

    def reverse(self, query, lang='en', exactly_one=True, timeout=None):
        """
        Given a point, find the 3 word address.

        :param query: The coordinates for which you wish to obtain the 3 word
            address.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param str lang: two character language codes as supported by the
            API (http://what3words.com/api/reference/languages).

        :param bool exactly_one: Parameter has no effect for this geocoder.
            Due to the address scheme there is always exactly one result.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        """
        lang = lang.lower()

        params = {
            'position': self._coerce_point_to_string(query),
            'lang': self.format_string % lang,
            'key': self.api_key,
        }

        url = "?".join(((self.api + "position"), urlencode(params)))

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_reverse_json(
            self._call_geocoder(url, timeout=timeout),
        )


    @staticmethod
    def _parse_reverse_json(resources):
        """
        Parses a location from a single-result reverse API call.
        """

        if resources.get('error') == "21":
            raise exc.GeocoderQueryError("Invalid coordinates")

        def parse_resource(resource):
            """
            Parse resource to return Geopy Location object
            """
            words = resource['words']
            words = join_filter(".", [words[0], words[1], words[2]])
            position = resource['position']
            latitude, longitude = position[0], position[1]

            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)

            return Location(words, (latitude, longitude), resource)

        return parse_resource(resources)







