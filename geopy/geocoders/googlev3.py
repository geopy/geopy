'''Google Maps V3 geocoder.

Largely adapted from the existing v2 geocoder with modifications made where
possible to support the v3 api as well as to clean up the class without
breaking its compatibility or diverging its api too far from the rest of the
geocoder classes.
'''

import base64
import hashlib
import hmac
from urllib import urlencode
from urllib2 import urlopen

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
    
    def __init__(self, domain='maps.googleapis.com', protocol='http',
                 client_id=None, secret_key=None):
        '''Initialize a customized Google geocoder.

        API authentication is only required for Google Maps Premier customers.

        ``domain`` should be the localized Google Maps domain to connect to. The default
        is 'maps.google.com', but if you're geocoding address in the UK (for
        example), you may want to set it to 'maps.google.co.uk' to properly bias results.

        ``protocol`` http or https.
        
        ``client_id`` Premier account client id.
        
        ``secret_key`` Premier account secret key.
        '''
        super(GoogleV3, self).__init__()

        if protocol not in ('http', 'https'):
            raise ValueError, 'Supported protocols are http and https.'
        if client_id and not secret_key:
            raise ValueError, 'Must provide secret_key with client_id.'
        if secret_key and not client_id:
            raise ValueError, 'Must provide client_id with secret_key.'

        self.domain = domain.strip('/')
        self.protocol = protocol
        self.doc = {}

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
                      'params': urlencode(params)}
        secret = base64.urlsafe_b64decode(self.secret_key)
        url_params['url_part'] = (
            '/maps/api/geocode/json?%(params)s' % url_params)
        signature = hmac.new(secret, url_params['url_part'], hashlib.sha1)
        url_params['signature'] = base64.urlsafe_b64encode(signature.digest())

        return ('%(protocol)s://%(domain)s%(url_part)s'
                '&signature=%(signature)s' % url_params)

    def get_url(self, params):
        '''Returns a standard geocoding api url.'''
        return 'http://%(domain)s/maps/api/geocode/json?%(params)s' % (
            {'domain': self.domain, 'params': urlencode(params)})
    
    def geocode_url(self, url, exactly_one=True):
        '''Fetches the url and returns the result.'''
        util.logger.debug("Fetching %s..." % url)
        page = urlopen(url)

        return self.parse_json(page, exactly_one)

    def geocode(self, string, bounds=None, region=None,
                language=None, sensor=False, exactly_one=True):
        '''Geocode an address.

        ``string`` (required) The address that you want to geocode.

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
        if isinstance(string, unicode):
            string = string.encode('utf-8')

        params = {
            'address': self.format_string % string,
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
