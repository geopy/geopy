try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json

from urllib import urlencode
from urllib2 import urlopen

from geopy.geocoders.base import Geocoder,GeocoderError,GeocoderResultError
from geopy import util

class GooglePlaces(Geocoder):
    """Geocoder using the Google Places API."""

    def __init__(self, api_key, format_string='%s', output_format=None):
        """Initialize a customized Google Places geocoder with location-specific
        address information and your Google Places API key.

        ``api_key`` should be a valid Google Places API key. (REQUIRED)

        ``format_string`` is a string containing '%s' where the string to
        geocode should be interpolated before querying the geocoder.
        For example: '%s, Mountain View, CA'. The default is just '%s'.

        ``output_format`` is set to json by default. Acceptable values are 
        'json' and 'xml'. (REQUIRED)
        
        ``sensor`` is set to 'false' by default and cannot (should not?) 
        be overriden, ideally. (REQUIRED)
        """
        if output_format:
            if output_format not in ('json','xml'):
                raise ValueError('if defined, `output_format` must be one of: "json","xml"')
            else:
                self.output_format = output_format
        else:
            self.output_format = "json"
        
        self.api_key = api_key
        self.format_string = format_string
        self.url = "https://maps.googleapis.com/maps/api/place/textsearch/%s?%%s" % self.output_format.lower()

    def geocode(self, string, sensor=False, exactly_one=True):
        params = {'query': self.format_string % string,
                  'sensor': str(sensor).lower(),
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
            places = doc.getElementsByTagName('results')

        if len(places) == 0 and doc is not None:
            # Got empty result. Parse out the status code and raise an error if necessary.
            status = doc.getElementsByTagName("results")
            status_code = int(util.get_first_text(status, 'status'))
            self.check_status_code(status_code)
        
        if exactly_one and len(places) != 1:
            raise ValueError("Didn't find exactly one placemark! " \
                             "(Found %d.)" % len(places))
        
        def parse_place(place):
            location = util.get_first_text(place, ['name', 'formatted_address']) or None
            points = place.getElementsByTagName('geometry')
            point = points and points[0] or None
            coords = util.get_first_text(point, 'location') or None
            if coords:
                latitude = util.get_first_text(coords, 'lat')
                longitude = util.get_first_text(coords, 'lng')
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
        places = doc.get('results', [])

        if len(places) == 0:
            # Got empty result. Parse out the status code and raise an error if necessary.
            status_code = doc.get("status", None)
            # status_code = status["code"]
            self.check_status_code(status_code)
            return None
        elif exactly_one and len(places) != 1:
            raise ValueError("Didn't find exactly one placemark! " \
                             "(Found %d.)" % len(places))

        def parse_place(place):
            location = place.get('formatted_address')
            latitude = place['geometry']['location']['lat']
            longitude = place['geometry']['location']['lng']
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
        elif status_code == 'INVALID_REQUEST':
            raise GQueryError("An empty lookup was performed. Additionally, Google says that a required query parameter (location or radius) is missing.")
        elif status_code == 'ZERO_RESULTS':
            raise GQueryError("No corresponding geographic location could be found for the specified location, possibly because the address is relatively new, or because it may be incorrect. Additionally, Google says that the search was successful but returned no results. This may occur if the search was passed a latlng in a remote location.")
        elif status_code == 'REQUEST_DENIED':
            raise GQueryError("The geocode for the given location could not be returned due to legal or contractual reasons. Additionally, Google says that your request was denied, generally because of lack of a sensor parameter.")
        elif status_code == 'OVER_QUERY_LIMIT':
            raise GTooManyQueriesError("The given key has gone over the requests limit in the 24 hour period or has submitted too many requests in too short a period of time. Additionally, Google says that you are over your quota")

class GBadKeyError(GeocoderError):
    pass

class GQueryError(GeocoderResultError):
    pass

class GTooManyQueriesError(GeocoderResultError):
    pass
