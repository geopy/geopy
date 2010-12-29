from urllib import urlencode
from urllib2 import urlopen
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json

import xml
from xml.parsers.expat import ExpatError

from geopy.geocoders.base import Geocoder,GeocoderError,GeocoderResultError
from geopy import Point, Location, util

class Google(Geocoder):
    """Geocoder using the Google Maps API."""
    
    def __init__(self, api_key=None, domain='maps.google.com',
                 resource=None, format_string='%s', output_format=None):
        """Initialize a customized Google geocoder with location-specific
        address information and your Google Maps API key.

        ``api_key`` should be a valid Google Maps API key. Required as per Google Geocoding API
        V2 docs, but the API works without a key in practice.

        ``domain`` should be the localized Google Maps domain to connect to. The default
        is 'maps.google.com', but if you're geocoding address in the UK (for
        example), you may want to set it to 'maps.google.co.uk' to properly bias results.

        ``resource`` is DEPRECATED and ignored -- the parameter remains for compatibility
        purposes.  The supported 'maps/geo' API is used regardless of this parameter.

        ``format_string`` is a string containing '%s' where the string to
        geocode should be interpolated before querying the geocoder.
        For example: '%s, Mountain View, CA'. The default is just '%s'.
        
        ``output_format`` (DEPRECATED) can be 'json', 'xml', or 'kml' and will
        control the output format of Google's response. The default is 'json'. 'kml' is
        an alias for 'xml'.
        """
        if resource != None:
            from warnings import warn
            warn('geopy.geocoders.google.GoogleGeocoder: The `resource` parameter is deprecated '+
                 'and now ignored. The Google-supported "maps/geo" API will be used.', DeprecationWarning)

        if output_format != None:
            from warnings import warn
            warn('geopy.geocoders.google.GoogleGeocoder: The `output_format` parameter is deprecated.', DeprecationWarning)

        self.api_key = api_key
        self.domain = domain
        self.format_string = format_string
        
        if output_format:
            if output_format not in ('json','xml','kml'):
                raise ValueError('if defined, `output_format` must be one of: "json","xml","kml"')
            else:
                if output_format == "kml":
                    self.output_format = "xml"
                else:
                    self.output_format = output_format
        else:
            self.output_format = "xml"

    @property
    def url(self):
        domain = self.domain.strip('/')
        return "http://%s/maps/geo?%%s" % domain

    def geocode(self, string, exactly_one=True):
        params = {'q': self.format_string % string,
                  'output': self.output_format.lower(),
                  }
        
        if self.api_key:
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
            doc = None
        else:
            places = doc.getElementsByTagName('Placemark')

        if len(places) == 0 and doc is not None:
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
            return [parse_place(place) for place in places]

    def parse_json(self, page, exactly_one=True):
        if not isinstance(page, basestring):
            page = util.decode_page(page)
        doc = json.loads(page)
        places = doc.get('Placemark', [])

        if len(places) == 0:
            # Got empty result. Parse out the status code and raise an error if necessary.
            status = doc.get("Status", [])
            status_code = status["code"]
            self.check_status_code(status_code)
            return None

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
            return [parse_place(place) for place in places]

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
