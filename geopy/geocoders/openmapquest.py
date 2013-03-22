try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json

from urllib import urlencode
from urllib2 import urlopen

from geopy.geocoders.base import Geocoder
from geopy.util import logger, decode_page, join_filter

class OpenMapQuest(Geocoder):
    """Geocoder using the MapQuest Open Platform Web Services."""
    
    def __init__(self, api_key='', format_string='%s'):
        """Initialize an Open MapQuest geocoder with location-specific
        address information, no API Key is needed by the Nominatim based
        platform.
        
        ``format_string`` is a string containing '%s' where the string to
        geocode should be interpolated before querying the geocoder.
        For example: '%s, Mountain View, CA'. The default is just '%s'.
        """
        
        self.api_key = api_key
        self.format_string = format_string
        self.url = "http://open.mapquestapi.com/nominatim/v1/search?format=json&%s"
    
    def geocode(self, string, exactly_one=True):
        if isinstance(string, unicode):
            string = string.encode('utf-8')
        params = {'q': self.format_string % string}
        url = self.url % urlencode(params)
        
        logger.debug("Fetching %s..." % url)
        page = urlopen(url)
        
        return self.parse_json(page, exactly_one)
    
    def parse_json(self, page, exactly_one=True):
        """Parse display name, latitude, and longitude from an JSON response."""
        if not isinstance(page, basestring):
            page = decode_page(page)
        resources = json.loads(page)
        
        if exactly_one and len(resources) != 1:
            from warnings import warn
            warn("Didn't find exactly one resource!" + \
                "(Found %d.), use exactly_one=False\n" % len(resources)
            )
            
        def parse_resource(resource):
            location = resource['display_name']
            
            latitude = resource['lat'] or None
            longitude = resource['lon'] or None
            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)
            
            return (location, (latitude, longitude))
        
        if exactly_one:
            return parse_resource(resources[0])
        else:
            return [parse_resource(resource) for resource in resources]
