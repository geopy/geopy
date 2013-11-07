"""
:class:`GeocoderDotUS` geocoder.
"""

import csv
import base64
from geopy.compat import urlencode, py3k
from geopy.geocoders.base import Geocoder, DEFAULT_FORMAT_STRING, \
    DEFAULT_TIMEOUT
from geopy.util import logger, join_filter
from geopy.exc import ConfigurationError
from urllib2 import Request, urlopen


class GeocoderDotUS(Geocoder): # pylint: disable=W0223
    """
    GeocoderDotUS geocoder, documentation at:
        http://geocoder.us/

    Note that GeocoderDotUS does not support SSL.
    """

    def __init__(self, username=None, password=None, # pylint: disable=R0913
                        format_string=DEFAULT_FORMAT_STRING,
                        timeout=DEFAULT_TIMEOUT, proxies=None):
        """
        :param string username:

        :param string password:

        :param string format_string: String containing '%s' where the
            string to geocode should be interpolated before querying the
            geocoder. For example: '%s, Mountain View, CA'. The default
            is just '%s'.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising an :class:`geopy.exc.GeocoderTimedOut`
            exception.

            .. versionadded:: 0.97

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

            .. versionadded:: 0.96
        """
        super(GeocoderDotUS, self).__init__(
            format_string=format_string, timeout=timeout, proxies=proxies
        )
        if username and (password is None):
            raise ConfigurationError("Password must be specified with username")
        self.username = username
        self.password = password

    def _get_url(self):
        if self.username and self.password:
            return 'http://geocoder.us/member/service/namedcsv'
        return 'http://geocoder.us/service/namedcsv'

    def geocode(self, query, exactly_one=True, timeout=None): # pylint: disable=W0613,W0221
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call only,
            the value set during the geocoder's initialization.

            .. versionadded:: 0.97
        """
        query_str = self.format_string % query

        request = Request(self._get_url(), urlencode({'address': query_str}))
        if self.username and self.password:
            request.add_header(
                'Authorization',
                'Basic %s' % base64.encodestring(
                    '%s:%s' % (self.username, self.password)).strip())
        page = self._call_geocoder(request, timeout=timeout, raw=True)
        content = page.read().decode("utf-8") if py3k else page.read()
        places = [r for r in csv.reader([content, ]
                  if not isinstance(content, list) else content)]
        if not len(places):
            return None
        if exactly_one is True:
            return self._parse_result(places[0])
        else:
            return [self._parse_result(res) for res in places]

    @staticmethod
    def _parse_result(result):
        """
        Parse individual results. Different, but lazy actually, so... ok.
        """
        # turn x=y pairs ("lat=47.6", "long=-117.426") into dict key/value pairs:
        place = dict(
            [x.split('=') for x in result if len(x.split('=')) > 1]
        )

        address = [
            place.get('number', None),
            place.get('prefix', None),
            place.get('street', None),
            place.get('type', None),
            place.get('suffix', None)
        ]
        city = place.get('city', None)
        state = place.get('state', None)
        zip_code = place.get('zip', None)

        name = join_filter(", ", [
            join_filter(" ", address),
            city,
            join_filter(" ", [state, zip_code])
        ])

        latitude = place.get('lat', None)
        longitude = place.get('long', None)
        if latitude and longitude:
            latlon = float(latitude), float(longitude)
        else:
            return None
        return name, latlon
