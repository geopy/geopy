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
    """What3Words geocoder.

    Documentation at:
        https://what3words.com/api/reference

    .. versionadded:: 1.5.0
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

        :param str api_key: Key provided by What3Words
            (https://accounts.what3words.com/register).

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
        Return a location point for a `3 words` query. If the `3 words` address
        doesn't exist, a :class:`geopy.exc.GeocoderQueryError` exception will be
        thrown.

        :param str query: The 3-word address you wish to geocode.

        :param str lang: two character language codes as supported by
            the API (https://docs.what3words.com/api/v2/#lang).

        :param bool exactly_one: Return one result or a list of results, if
            available. Due to the address scheme there is always exactly one
            result for each `3 words` address, so this parameter is rather
            useless for this geocoder.

            .. versionchanged:: 1.14.0
               ``exactly_one=False`` now returns a list of a single location.
               This option wasn't respected before.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
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
            exactly_one=exactly_one
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
                # TODO this branch probably needs to be removed, as OneWord
                # addresses have been canceled.
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

        location = parse_resource(resources)
        if exactly_one:
            return location
        else:
            return [location]

    def reverse(self, query, lang='en', exactly_one=True,
                timeout=DEFAULT_SENTINEL):
        """
        Return a `3 words` address by location point. Each point on surface has
        a `3 words` address, so there's always a non-empty response.

        :param query: The coordinates for which you wish to obtain the 3 word
            address.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param str lang: two character language codes as supported by the
            API (https://docs.what3words.com/api/v2/#lang).

        :param bool exactly_one: Return one result or a list of results, if
            available. Due to the address scheme there is always exactly one
            result for each `3 words` address, so this parameter is rather
            useless for this geocoder.

            .. versionchanged:: 1.14.0
               ``exactly_one=False`` now returns a list of a single location.
               This option wasn't respected before.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

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
            exactly_one=exactly_one
        )

    def _parse_reverse_json(self, resources, exactly_one=True):
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

        location = parse_resource(resources)
        if exactly_one:
            return location
        else:
            return [location]
