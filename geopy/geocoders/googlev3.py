'''Google Maps V3 geocoder.'''
import base64
import hashlib
import hmac
from urllib import urlencode
from urllib2 import urlopen
from xml import dom
from xml.parsers.expat import ExpatError

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json

from geopy.geocoders.base import Geocoder, GeocoderResultError
from geopy import util



class GoogleV3(Geocoder):
    '''Geocoder using the Google Maps v3 API.'''
    
    def __init__(self, domain='maps.googleapis.com', format_string='%s',
                 output_format='json', protocol='http', client_id=None,
                 secret_key=None):
        '''Initialize a customized Google geocoder.

        API authentication is only required for Google Maps Premier customers.

        ``domain`` should be the localized Google Maps domain to connect to. The default
        is 'maps.google.com', but if you're geocoding address in the UK (for
        example), you may want to set it to 'maps.google.co.uk' to properly bias results.

        ``format_string`` is a string containing '%s' where the string to
        geocode should be interpolated before querying the geocoder.
        For example: '%s, Mountain View, CA'. The default is just '%s'.
        
        ``output_format`` can be 'json' or 'xml' The default is 'json'.
        
        ``protocol`` http or https.
        
        ``client_id`` Premier account client id.
        
        ``secret_key`` Premier account secret key.
        '''
        super(GoogleV3, self).__init__()

        if protocol not in ('http', 'https'):
            raise ValueError, 'Supported protocols are http and https.'
        if output_format not in ('json', 'xml'):
            raise ValueError, 'Supported output_formats are json and xml.'
        if client_id and not secret_key:
            raise ValueError, 'Must provide secret_key with client_id.'
        if secret_key and not client_id:
            raise ValueError, 'Must provide client_id with secret_key.'

        self.domain = domain.strip('/')
        self.format_string = format_string
        self.protocol = protocol
        self.format = output_format

        if client_id and secret_key:
            self.client_id = client_id
            self.secret_key = secret_key
            self.premier = True
        else:
            self.premier = False

    def get_signed_url(self, params):
        '''Returns a Premier account signed url.'''
        params['client'] = self.client_id
        url_params = {'protocol': self.protocol, 'domain': self.domain,
                      'format': self.format, 'params': urlencode(params)}
        secret = base64.urlsafe_b64decode(self.secret_key)
        url_params['url_part'] = (
            '/maps/api/geocode/%(format)s?%(params)s' % url_params)
        signature = hmac.new(secret, url_params['url_part'], hashlib.sha1)
        url_params['signature'] = base64.urlsafe_b64encode(signature.digest())

        return ('%(protocol)s://%(domain)s%(url_part)s'
                '&signature=%(signature)s' % url_params)

    def get_url(self, params):
        '''Returns a standard geocoding api url.'''
        return 'http://%(domain)s/maps/api/geocode/%(format)s?%(params)s' % (
            {'domain': self.domain, 'format': self.format,
             'params': urlencode(params)})
    
    def geocode_url(self, url, exactly_one=True):
        '''Fetches the url and returns the result.'''
        util.logger.debug("Fetching %s..." % url)
        page = urlopen(url)

        if self.format == 'xml':
            dispatch = self.parse_xml
        elif self.format == 'json':
            dispatch = self.parse_json

        return dispatch(page, exactly_one)

    def geocode(self, address, bounds=None, region=None,
                language=None, sensor=False, exactly_one=True):
        '''Geocode an address.

        ``address`` (required) The address that you want to geocode.

        ``bounds`` (optional) The bounding box of the viewport within which
        to bias geocode results more prominently.

        ``region`` (optional) The region code, specified as a ccTLD
        ("top-level domain") two-character value.

        ``language`` (optional) The language in which to return results.
        See the supported list of domain languages. Note that we often update
        supported languages so this list may not be exhaustive. If language is
        not supplied, the geocoder will attempt to use the native language of
        the domain from which the request is sent wherever possible.

        ``sensor`` (required) Indicates whether or not the geocoding request
        comes from a device with a location sensor.
        This value must be either True or False.
        '''

        params = {
            'address': self.format_string % address,
            'sensor': str(sensor).lower()
        }

        if bounds:
            params['bounds'] = bounds
        if region:
            params['region'] = region
        if language:
            params['language'] = language

        if not self.premier:
            url = self.get_url(params)
        else:
            url = self.get_signed_url(params)

        return self.geocode_url(url, exactly_one)

    def reverse(self, point, language=None, sensor=False, exactly_one=False):
        '''Reverse geocode a point.
        ``point`` (required) The textual latitude/longitude value for which
        you wish to obtain the closest, human-readable address
        
        ``language`` (optional) The language in which to return results.
        See the supported list of domain languages. Note that we often update
        supported languages so this list may not be exhaustive. If language is
        not supplied, the geocoder will attempt to use the native language of
        the domain from which the request is sent wherever possible.

        ``sensor`` (required) Indicates whether or not the geocoding request
        comes from a device with a location sensor.
        This value must be either True or False.
        '''
        params = {
            'latlng': point,
            'sensor': str(sensor).lower()
        }

        if language:
            params['language'] = language

        if not self.premier:
            url = self.get_url(params)
        else:
            url = self.get_signed_url(params)

        return self.geocode_url(url, exactly_one)

    def parse_xml(self, page, exactly_one=True):
        '''Returns location, (latitude, longitude) from xml feed.'''
        if not isinstance(page, basestring):
            page = util.decode_page(page)
        try:
            self.doc = dom.minidom.parseString(page)
        except ExpatError:
            places = []
            self.doc = None
        else:
            places = self.doc.getElementsByTagName('result')
    
        if len(places) == 0 and self.doc is not None:
            # Got empty result.
            status = self.doc.getElementsByTagName("status")
            check_status(status)
        if exactly_one and len(places) != 1:
            raise ValueError(
                "Didn't find exactly one placemark! (Found %d)" % len(places))
    
        def parse_place(place):
            '''Get the location, lat and lng from a single place xml.'''
            location = util.get_first_text(place, ['formatted_address'])
            points = place.getElementsByTagName('location')[0]
            latitude = float(util.get_first_text(points, 'lat'))
            longitude = float(util.get_first_text(points, 'lng'))
            return (location, (latitude, longitude))
    
        if exactly_one:
            return parse_place(places[0])
        else:
            return [parse_place(place) for place in places]
    
    def parse_json(self, page, exactly_one=True):
        '''Returns location, (latitude, longitude) from json feed.'''
        if not isinstance(page, basestring):
            page = util.decode_page(page)
        self.doc = json.loads(page)
        places = self.doc.get('results', [])
    
        if not places:
            check_status(self.doc.get('status'))
            return None
        elif exactly_one and len(places) != 1:
            raise ValueError(
                "Didn't find exactly one placemark! (Found %d)" % len(places))
    
        def parse_place(place):
            '''Get the location, lat, lng from a single json place.'''
            location = place.get('formatted_address')
            latitude = place['geometry']['location']['lat']
            longitude = place['geometry']['location']['lng']
            return (location, (latitude, longitude))
        
        if exactly_one:
            return parse_place(places[0])
        else:
            return [parse_place(place) for place in places]

def check_status(status):
    '''Validates error statuses.'''
    if status == 'ZERO_RESULTS':
        raise GQueryError(
            'The geocode was successful but returned no results. This may'
            ' occur if the geocode was passed a non-existent address or a'
            ' latlng in a remote location.')
    elif status == 'OVER_QUERY_LIMIT':
        raise GTooManyQueriesError(
            'The given key has gone over the requests limit in the 24'
            ' hour period or has submitted too many requests in too'
            ' short a period of time.')
    elif status == 'REQUEST_DENIED':
        raise GQueryError(
            'Your request was denied, probably because of lack of a'
            ' sensor parameter.')
    elif status == 'INVALID_REQUEST':
        raise GQueryError('Probably missing address or latlng.')
    else:
        raise GeocoderResultError('Unkown error.')


class GQueryError(GeocoderResultError):
    '''Generic Google query error.'''
    pass

class GTooManyQueriesError(GeocoderResultError):
    '''Raised when the query rate limit is hit.'''
    pass
