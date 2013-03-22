from urllib import urlencode
from urllib2 import urlopen
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json

from geopy.geocoders.base import Geocoder,GeocoderError,GeocoderResultError
from geopy import Point, Location, util

from warnings import warn

class Google(Geocoder):
    """Geocoder using the Google Maps API."""
    
    def __init__(self, api_key=None, domain='maps.googleapis.com',
                 format_string='%s'):
        """Initialize a customized Google geocoder with location-specific
        address information and your Google Maps API key.

        ``api_key`` should be a valid Google Maps API key. Required as per Google Geocoding API
        V2 docs, but the API works without a key in practice.

        ``domain`` should be the localized Google Maps domain to connect to. The default
        is 'maps.google.com', but if you're geocoding address in the UK (for
        example), you may want to set it to 'maps.google.co.uk' to properly bias results.

        ``format_string`` is a string containing '%s' where the string to
        geocode should be interpolated before querying the geocoder.
        For example: '%s, Mountain View, CA'. The default is just '%s'.
        """
        
        warn('geopy.geocoders.google: The `geocoders.google.Google` geocoder uses the '+
            'older "V2" API and is deprecated and may be broken at any time. A '+
            'geocoder utilizing the "V3" API is available at '+
            '`geocoders.googlev3.GoogleV3` and will become the default in a future '+
            'version. See RELEASES file and http://goo.gl/somDT for usage information.',
            DeprecationWarning
        )
        
        if not api_key:
            raise ValueError(
                "The `geocoders.google.Google` (V2) API now requires the "+
                "`api_key` argument. Please acquire and use an API key "+
                "(http://goo.gl/EdoHX) or upgrade to "+
                "the V3 API (`geocoders.googlev3.GoogleV3`), which does "+
                "not require a key. ---- Please note that the V2 API is " +
                "deprecated and may not work after March 2013 or September 2013."
            )
        if domain == "maps.google.com":
            raise ValueError(
                "The `geocoders.google.Google` (V2) API now requires the "+
                "`domain` argument to be set to 'maps.googleapis.com'. Please "+
                "change or remove your `domain` kwarg."
            )

        self.api_key = api_key
        self.domain = domain
        self.format_string = format_string
        self.output_format = "json"

    @property
    def url(self):
        domain = self.domain.strip('/')
        return "http://%s/maps/geo?%%s" % domain

    def geocode(self, string, exactly_one=True):
        if isinstance(string, unicode):
            string = string.encode('utf-8')
        params = {'q': self.format_string % string,
                  'output': self.output_format.lower(),
                  'key': self.api_key,
                  'sensor': False
                  }
        
        url = self.url % urlencode(params)
        return self.geocode_url(url, exactly_one)

    def geocode_url(self, url, exactly_one=True):
        util.logger.debug("Fetching %s..." % url)
        page = urlopen(url)
        
        dispatch = getattr(self, 'parse_' + self.output_format)
        return dispatch(page, exactly_one)

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
        elif exactly_one and len(places) != 1:
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
