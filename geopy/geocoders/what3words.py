"""
:class:`.What3Words` geocoder.
"""

import re

from geopy import exc
from geopy.compat import urlencode
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import join_filter, logger

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
            format_string=None,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
    ):
        """
        Initialize a What3Words geocoder with 3-word or OneWord-address and
        What3Words API key.

            .. versionadded:: 1.5.0

        :param str api_key: Key provided by What3Words.

        :param str format_string:
            See :attr:`geopy.geocoders.options.default_format_string`.

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str user_agent:
            See :attr:`geopy.geocoders.options.default_user_agent`.

            .. versionadded:: 1.12.0

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.

            .. versionadded:: 1.14.0
        """
        super(What3Words, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
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
                timeout=DEFAULT_SENTINEL):

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
        """

        if not self._check_query(query):
            raise exc.GeocoderQueryError(
                "Search string must be either like "
                "'word.word.word' or '*word' "
            )

        params = {
            'string': self.format_string % query,
            'lang': lang.lower(),
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

    def reverse(self, query, lang='en', exactly_one=True,
                timeout=DEFAULT_SENTINEL):
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
            'lang': lang.lower(),
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
