from urllib import urlencode
from urllib2 import urlopen
try:
    import json as simplejson
except ImportError:
    import simplejson

import xml
from xml.parsers.expat import ExpatError

from geopy.geocoders.base import Geocoder,GeocoderError,GeocoderResultError
from geopy import Point, Location, util

class Google(Geocoder):
    """Geocoder using the Google Maps API."""
    
    def __init__(self, api_key=None, domain='maps.google.com',
                 resource='maps/geo', format_string='%s', output_format='kml'):
        """Initialize a customized Google geocoder with location-specific
        address information and your Google Maps API key.

        ``api_key`` should be a valid Google Maps API key. It is required for
        the 'maps/geo' resource to work.

        ``domain`` should be a the Google Maps domain to connect to. The default
        is 'maps.google.com', but if you're geocoding address in the UK (for
        example), you may want to set it to 'maps.google.co.uk'.

        ``resource`` is the HTTP resource to give the query parameter.
        'maps/geo' is the HTTP geocoder and is a documented API resource.
        'maps' is the actual Google Maps interface and its use for just
        geocoding is undocumented. Anything else probably won't work.

        ``format_string`` is a string containing '%s' where the string to
        geocode should be interpolated before querying the geocoder.
        For example: '%s, Mountain View, CA'. The default is just '%s'.
        
        ``output_format`` can be 'json', 'xml', 'kml', 'csv', or 'js' and will
        control the output format of Google's response. The default is 'kml'
        since it is supported by both the 'maps' and 'maps/geo' resources. The
        'js' format is the most likely to break since it parses Google's
        JavaScript, which could change. However, it currently returns the best
        results for restricted geocoder areas such as the UK.
        """
        self.api_key = api_key
        self.domain = domain
        self.resource = resource
        self.format_string = format_string
        self.output_format = output_format

    @property
    def url(self):
        domain = self.domain.strip('/')
        resource = self.resource.strip('/')
        return "http://%(domain)s/%(resource)s?%%s" % locals()

    def geocode(self, string, exactly_one=True):
        params = {'q': self.format_string % string,
                  'output': self.output_format.lower(),
                  }
        if self.resource.rstrip('/').endswith('geo'):
            # An API key is only required for the HTTP geocoder.
            params['key'] = self.api_key

        url = self.url % urlencode(params)
        return self.geocode_url(url, exactly_one)

    def geocode_url(self, url, exactly_one=True):
        util.logger.debug("Fetching %s..." % url)
        page = urlopen(url)
        
        dispatch = getattr(self, 'parse_' + self.output_format)
        return dispatch(page, exactly_one)

    def parse_xml(self, page, exactly_one=True):
        """Parse a location name, latitude, and longitude from an XML response.
        """
        if not isinstance(page, basestring):
            page = util.decode_page(page)
        try:
            doc = xml.dom.minidom.parseString(page)
        except ExpatError:
            places = []
        else:
            places = doc.getElementsByTagName('Placemark')

        if len(places) == 0:
            # Got empty result. Parse out the status code and raise an error if necessary.
            status = doc.getElementsByTagName("Status")
            status_code = int(util.get_first_text(status[0], 'code'))
            self.check_status_code(status_code)
        
        if exactly_one and len(places) != 1:
            raise ValueError("Didn't find exactly one placemark! " \
                             "(Found %d.)" % len(places))
        
        def parse_place(place):
            location = util.get_first_text(place, ['address', 'name']) or None
            points = place.getElementsByTagName('Point')
            point = points and points[0] or None
            coords = util.get_first_text(point, 'coordinates') or None
            if coords:
                longitude, latitude = [float(f) for f in coords.split(',')[:2]]
            else:
                latitude = longitude = None
                _, (latitude, longitude) = self.geocode(location)
            return (location, (latitude, longitude))
        
        if exactly_one:
            return parse_place(places[0])
        else:
            return (parse_place(place) for place in places)

    def parse_csv(self, page, exactly_one=True):
        raise NotImplementedError

    def parse_kml(self, page, exactly_one=True):
        return self.parse_xml(page, exactly_one)

    def parse_json(self, page, exactly_one=True):
        if not isinstance(page, basestring):
            page = util.decode_page(page)
        json = simplejson.loads(page)
        places = json.get('Placemark', [])

        if len(places) == 0:
            # Got empty result. Parse out the status code and raise an error if necessary.
            status = json.get("Status", [])
            status_code = status["code"]
            self.check_status_code(status_code)

        if exactly_one and len(places) != 1:
            raise ValueError("Didn't find exactly one placemark! " \
                             "(Found %d.)" % len(places))

        def parse_place(place):
            location = place.get('address')
            longitude, latitude = place['Point']['coordinates'][:2]
            return (location, (latitude, longitude))
        
        if exactly_one:
            return parse_place(places[0])
        else:
            return (parse_place(place) for place in places)

    def parse_js(self, page, exactly_one=True):
        """This parses JavaScript returned by queries the actual Google Maps
        interface and could thus break easily. However, this is desirable if
        the HTTP geocoder doesn't work for addresses in your country (the
        UK, for example).
        """
        if not isinstance(page, basestring):
            page = util.decode_page(page)

        LATITUDE = r"[\s,]lat:\s*(?P<latitude>-?\d+\.\d+)"
        LONGITUDE = r"[\s,]lng:\s*(?P<longitude>-?\d+\.\d+)"
        LOCATION = r"[\s,]laddr:\s*'(?P<location>.*?)(?<!\\)',"
        ADDRESS = r"(?P<address>.*?)(?:(?: \(.*?@)|$)"
        MARKER = '.*?'.join([LATITUDE, LONGITUDE, LOCATION])
        MARKERS = r"{markers: (?P<markers>\[.*?\]),\s*polylines:"            

        def parse_marker(marker):
            latitude, longitude, location = marker
            location = re.match(ADDRESS, location).group('address')
            latitude, longitude = float(latitude), float(longitude)
            return (location, (latitude, longitude))

        match = re.search(MARKERS, page)
        markers = match and match.group('markers') or ''
        markers = re.findall(MARKER, markers)
       
        if exactly_one:
            if len(markers) != 1:
                raise ValueError("Didn't find exactly one marker! " \
                                 "(Found %d.)" % len(markers))
            
            marker = markers[0]
            return parse_marker(marker)
        else:
            return (parse_marker(marker) for marker in markers)

    def check_status_code(self,status_code):
        if status_code == 400:
            raise GeocoderResultError("Bad request (Server returned status 400)")
        elif status_code == 500:
            raise GeocoderResultError("Unkown error (Server returned status 500)")
        elif status_code == 601:
            raise GQueryError("An empty lookup was performed")
        elif status_code == 602:
            raise GQueryError("No corresponding geographic location could be found for the specified location, possibly because the address is relatively new, or because it may be incorrect.")
        elif status_code == 603:
            raise GQueryError("The geocode for the given location could be returned due to legal or contractual reasons")
        elif status_code == 610:
            raise GBadKeyError("The api_key is either invalid or does not match the domain for which it was given.")
        elif status_code == 620:
            raise GTooManyQueriesError("The given key has gone over the requests limit in the 24 hour period or has submitted too many requests in too short a period of time.")

class GBadKeyError(GeocoderError):
    pass

class GQueryError(GeocoderResultError):
    pass

class GTooManyQueriesError(GeocoderResultError):
    pass
