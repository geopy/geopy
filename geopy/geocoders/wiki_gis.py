"""
:class:`.MediaWiki` geocoder.
"""

from geopy.compat import BeautifulSoup

from geopy.geocoders.base import Geocoder
from geopy.util import logger, parse_geo


class MediaWiki(Geocoder): # pylint: disable=W0223
    """
    MediaWiki geocoder. No idea on documentation.
    """

    def __init__(self, format_url, transform_string=None, proxies=None):
        """
        Initialize a geocoder that can parse MediaWiki pages with the GIS
        extension enabled.

        :param string format_url: is a URL string containing '%s' where the
            page name to request will be interpolated. For
            example: 'http://www.wiki.com/wiki/%s'

        :param callable _transform_string: is a callable that will make
            appropriate replacements to the input string before requesting
            the page. If ``None`` is given, the default _transform_string
            which replaces ' ' with '_' will be used.
        """
        super(MediaWiki, self).__init__(proxies=proxies)
        self.format_url = format_url
        if transform_string:
            self._transform_string = transform_string

    @staticmethod
    def _transform_string(string): # pylint: disable=E0202
        """Do the WikiMedia dance: replace spaces with underscores."""
        return string.replace(' ', '_')

    def geocode(self, query):
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.
        """
        wiki_string = self._transform_string(query)
        url = self.format_url % wiki_string
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self.geocode_url(url)

    def geocode_url(self, url):
        logger.debug("Fetching %s...", url)
        page = self.urlopen(url)
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
