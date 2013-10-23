"""
:class:`.MediaWiki` geocoder.
"""

from urllib2 import urlopen

from geopy.geocoders.base import Geocoder
from geopy.util import logger, parse_geo

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    BeautifulSoup = None # pylint: disable=C0103

class MediaWiki(Geocoder):
    def __init__(self, format_url, transform_string=None):
        """Initialize a geocoder that can parse MediaWiki pages with the GIS
        extension enabled.

        ``format_url`` is a URL string containing '%s' where the page name to
        request will be interpolated. For example: 'http://www.wiki.com/wiki/%s'

        ``transform_string`` is a callable that will make appropriate
        replacements to the input string before requesting the page. If None is
        given, the default transform_string which replaces ' ' with '_' will be
        used. It is recommended that you consider this argument keyword-only,
        since subclasses will likely place it last.
        """
        if not BeautifulSoup:
            raise ImportError(
                "BeautifulSoup was not found. Please install BeautifulSoup "
                "in order to use the MediaWiki Geocoder."
            )
        super(MediaWiki, self).__init__()
        self.format_url = format_url

        if callable(transform_string):
            self.transform_string = transform_string

    @classmethod
    def transform_string(cls, string):
        """Do the WikiMedia dance: replace spaces with underscores."""
        return string.replace(' ', '_')

    def geocode(self, string):
        if isinstance(string, unicode):
            string = string.encode('utf-8')
        wiki_string = self.transform_string(string)
        url = self.format_url % wiki_string
        return self.geocode_url(url)

    def geocode_url(self, url):
        logger.debug("Fetching %s..." % url)
        page = urlopen(url)
        name, (latitude, longitude) = self.parse_xhtml(page)
        return (name, (latitude, longitude))

    def parse_xhtml(self, page):
        soup = isinstance(page, BeautifulSoup) and page or BeautifulSoup(page)

        meta = soup.head.find('meta', {'name': 'geo.placename'})
        name = meta and meta['content'] or None

        meta = soup.head.find('meta', {'name': 'geo.position'})
        if meta:
            position = meta['content']
            # no parse_geo? TODO
            latitude, longitude = parse_geo(position)
            if latitude == 0 or longitude == 0:
                latitude = longitude = None
        else:
            latitude = longitude = None

        return (name, (latitude, longitude))
