"""
:class:`.GeoCoder` base object from which other geocoders are templated.
"""

import urllib2


class Geocoder(object):
    """
    Template object for geocoders.
    """

    def __init__(self, format_string=None):
        self.format_string = format_string or '%s'

        # Add urllib proxy support using environment variables or
        # built in OS proxy details
        # See: http://docs.python.org/2/library/urllib2.html
        # And: http://stackoverflow.com/questions/1450132/proxy-with-urllib2
        proxy = urllib2.ProxyHandler()
        opener = urllib2.build_opener(proxy)
        urllib2.install_opener(opener)

    def geocode(self, location):
        """
        Implemented in subclasses.
        """
        raise NotImplementedError()

    def reverse(self, point):
        """
        Implemented in subclasses.
        """
        raise NotImplementedError()

    def geocode_one(self, location):
        results = self.geocode(location)
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

    def geocode_first(self, location):
        results = self.geocode(location)
        for result in results:
            return result
        return None

class GeocoderError(Exception):
    pass

class GeocoderResultError(GeocoderError):
    pass
