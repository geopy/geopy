"""
:class:`GeocoderDotUS` geocoder.
"""

import csv
from geopy.compat import urlencode, py3k
from geopy.geocoders.base import Geocoder
from geopy.util import logger, join_filter
from geopy.exc import ConfigurationError


class GeocoderDotUS(Geocoder): # pylint: disable=W0223
    """
    GeoCoderDotUS geocoder, documentation at:
        http://geocoder.us/
    """

    def __init__(self, username=None, password=None, format_string=None, proxies=None):
        super(GeocoderDotUS, self).__init__(format_string, proxies)
        if username and password is None:
            raise ConfigurationError("password must be specified with username")
        self.username = username
        self.__password = password

    def _get_url(self):
        """
        Generate full query URL.
        """
        username = self.username
        password = self.__password
        if username and password:
            auth = '%s@%s:' % (username, password)
            resource = 'member/service/namedcsv'
        else:
            auth = ''
            resource = 'service/namedcsv'

        return 'http://%sgeocoder.us/%s' % (auth, resource)

    def geocode(self, query, exactly_one=True): # pylint: disable=W0613,W0221
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.
        """
        query_str = self.format_string % query

        url = "?".join((self._get_url(), urlencode({'address':query_str})))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)

        page = self._call_geocoder(url, raw=True)
        page = page.read().decode("utf-8") if py3k else page.read()
        places = [r for r in csv.reader([page, ] if not isinstance(page, list) else page)]
        if not len(places):
            return None
        if exactly_one is True:
            return self._parse_result(places[0])
        else:
            return [self._parse_result(res) for res in places]

    @staticmethod
    def _parse_result(result):
        """
        TODO docs, accept iterable
        """
        # turn x=y pairs ("lat=47.6", "long=-117.426") into dict key/value pairs:
        place = dict(
            # strip off bits that aren't pairs (i.e. "geocoder modified" status string")
            filter(lambda x: len(x)>1, # pylint: disable=W0141
            # split the key=val strings into (key, val) tuples
            map(lambda x: x.split('=', 1), result) # pylint: disable=W0141
        ))

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
