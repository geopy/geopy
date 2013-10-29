"""
:class:`.GeoCoder` base object from which other geocoders are templated.
"""

try:
    from urllib2 import urlopen as urllib_urlopen, build_opener, ProxyHandler
except ImportError:
    from urllib.request import (urlopen as urllib_urlopen, # pylint: disable=F0401,E0611
        build_opener, ProxyHandler)
from warnings import warn

from geopy.compat import py3k, string_compare, HTTPError, json
from geopy.point import Point
from geopy.exc import GeocoderServiceError, ConfigurationError
from geopy.util import decode_page

DEFAULT_FORMAT_STRING = '%s'
DEFAULT_SCHEME = 'https'
DEFAULT_TIMEOUT = 10


class Geocoder(object): # pylint: disable=R0921
    """
    Template object for geocoders.
    """

    def __init__(self, format_string='%s', scheme='https', timeout=DEFAULT_TIMEOUT, proxies=None):
        """
        Mostly-common geocoder validation, proxies, &c. Not all geocoders
        specify format_string and such.
        """
        self.format_string = format_string
        self.scheme = scheme
        if self.scheme not in ('http', 'https'):
            raise ConfigurationError('Supported schemes are `http` and `https`.')
        self.proxies = proxies
        self.timeout = timeout

        # Add urllib proxy support using environment variables or
        # built in OS proxy details
        # See: http://docs.python.org/2/library/urllib2.html
        # And: http://stackoverflow.com/questions/1450132/proxy-with-urllib2
        if self.proxies is None:
            self.urlopen = urllib_urlopen
        else:
            self.urlopen = build_opener(
                ProxyHandler(self.proxies)
            )

    @staticmethod
    def _coerce_point_to_string(point):
        """
        Do the right thing on "point" input. For geocoders with reverse
        methods.
        """
        if isinstance(point, Point):
            return ",".join((str(point.latitude), str(point.longitude)))
        elif isinstance(point, (list, tuple)):
            return ",".join((str(point[0]), str(point[1]))) # -altitude
        elif isinstance(point, string_compare):
            return point
        else:
            raise ValueError("Invalid point")

    def _parse_json(self, page, exactly_one):
        """
        Template for subclasses
        """
        raise NotImplementedError()

    def parse_json(self, *args, **kwargs):
        """
        Compatibility until 0.97.0
        """
        warn(
            "parse_json is now a private method at _parse_json; this name "
            "will be removed in the next non-bugfix release"
        )
        return self._parse_json(*args, **kwargs)

    def _call_geocoder(self, url, timeout=None, raw=False):
        """
        For a generated query URL, get the results.
        """
        try:
            page = self.urlopen(url, timeout=timeout or self.timeout)
        except HTTPError as error:
            if hasattr(self, '_geocoder_exception_handler'):
                self._geocoder_exception_handler(error) # pylint: disable=E1101
            raise GeocoderServiceError(error.getcode(), getattr(error, 'msg', None))
        if raw:
            return page
        return json.loads(decode_page(page))

    def geocode(self, query, exactly_one=True, timeout=None): # pylint: disable=R0201,W0613
        """
        Implemented in subclasses. Just string coercion here.
        """
        if not py3k and isinstance(query, unicode):
            query = query.encode('utf-8')

    def reverse(self, query, exactly_one=True, timeout=None):
        """
        Implemented in subclasses.
        """
        raise NotImplementedError()

    def geocode_one(self, query): # pylint: disable=C0111
        warn(
            "geocode_one is deprecated and will be removed in the next"
            "non-bugfix release. Call geocode with exactly_one=True instead."
        )
        results = self.geocode(query)
        first = None
        for result in results:
            if first is None:
                first = result
            else:
                raise GeocoderResultError(
                    "Geocoder returned more than one result!"
                )
        if first is not None:
            return first
        else:
            raise GeocoderResultError("Geocoder returned no results!")

    def geocode_first(self, query): # pylint: disable=C0111
        warn(
            "geocode_first is deprecated and will be removed in the next"
            "non-bugfix release. Call geocode with exactly_one=True instead."
        )
        results = self.geocode(query)
        for result in results:
            return result
        return None


class GeocoderError(Exception): # pylint: disable=C0111
    pass

class GeocoderResultError(GeocoderError): # pylint: disable=C0111
    pass
