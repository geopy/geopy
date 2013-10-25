"""
:class:`.GeoCoder` base object from which other geocoders are templated.
"""

import urllib2
from warnings import warn

from geopy.compat import py3k
from geopy.point import Point


class Geocoder(object): # pylint: disable=R0921
    """
    Template object for geocoders.
    """

    def __init__(self, format_string=None, proxies=None):
        self.format_string = format_string or '%s'
        self.proxies = proxies

        # Add urllib proxy support using environment variables or
        # built in OS proxy details
        # See: http://docs.python.org/2/library/urllib2.html
        # And: http://stackoverflow.com/questions/1450132/proxy-with-urllib2
        if self.proxies is None:
            self.urlopen = urllib2.urlopen
        else:
            self.urlopen = urllib2.build_opener(
                urllib2.ProxyHandler(self.proxies)
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
        elif isinstance(point, (str, unicode)):
            return point
        else:
            raise ValueError("Invalid point")


    def geocode(self, query, exactly_one=True): # pylint: disable=R0201,W0613
        """
        Implemented in subclasses. Just string coercion here.
        """
        if isinstance(query, unicode) and not py3k:
            query = query.encode('utf-8')

    def reverse(self, query, exactly_one=True):
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
