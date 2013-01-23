'''
Google Time Zone API geocoder.

Based off the Google v3 API geocoder.

https://developers.google.com/maps/documentation/timezone/

'''

import time
from urllib import urlencode
from urllib2 import urlopen

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json

from geopy.geocoders.base import GeocoderResultError
from geopy.geocoders.googlev3 import GoogleV3
from geopy import util



class GoogleTimezone(GoogleV3):

    def get_url(self, params):
        '''Returns a standard geocoding api url.'''
        return 'http://%(domain)s/maps/api/timezone/json?%(params)s' % (
            {'domain': self.domain, 'params': urlencode(params)})
    
    def geocode_url(self, url):
        '''Fetches the url and returns the result.'''
        util.logger.debug("Fetching %s..." % url)
        page = urlopen(url)

        return self.parse_json(page)

    def geocode(self, latitude=None, longitude=None, timestamp=None,
                sensor=False, language=None):
        '''Geocode an lat/long into a timezone.

        ``latitude`` (required) The latitude of the location to geocode

        ``longitude`` (required) The longitude of the location to geocode

        ``timestamp`` (optional) A unix timestamp representing a point in 
        time determining whether DST should be applied.

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
            'location': str(latitude) + ',' + str(longitude)
            'sensor': str(sensor).lower()
        }

        if not timestamp:
            # default timestamp to today in unix time
            timestamp = int(time.time())
        params['timestamp'] = timestamp

        if language:
            params['language'] = language

        if not self.premier:
            url = self.get_url(params)
        else:
            url = self.get_signed_url(params)

        return self.geocode_url(url)

    def reverse(self, **kwargs):
        raise NotImplementedError

    def parse_json(self, page):
        '''Returns timezone (as Olsen format) from json feed.'''
        if not isinstance(page, basestring):
            page = util.decode_page(page)
        self.doc = json.loads(page)
        timezone = self.doc.get('timeZoneId')

        if not timezone:
            check_status(self.doc.get('status'))
            return None

        return timezone 

def check_status(status):
    '''Validates error statuses.'''
    if status == 'ZERO_RESULTS':
        raise GQueryError(
            'There is no time zone data for the given location.')
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
        raise GQueryError('Probably missing latitude/longitude.')
    else:
        raise GeocoderResultError('Unknown error.')


class GQueryError(GeocoderResultError):
    '''Generic Google query error.'''
    pass

class GTooManyQueriesError(GeocoderResultError):
    '''Raised when the query rate limit is hit.'''
    pass
