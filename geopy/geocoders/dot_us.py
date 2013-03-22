import getpass
from urllib import urlencode
from urllib2 import urlopen
from geopy.geocoders.base import Geocoder
from geopy import util
import csv

class GeocoderDotUS(Geocoder):
    def __init__(self, username=None, password=None, format_string='%s'):
        if username and (password is None):
            password = getpass.getpass(
                "geocoder.us password for %r: " % username
            )
        
        self.format_string = format_string
        self.username = username
        self.__password = password
    
    def get_url(self):
        username = self.username
        password = self.__password
        if username and password:
            auth = '%s@%s:' % (username, password)
            resource = 'member/service/namedcsv'
        else:
            auth = ''
            resource = 'service/namedcsv'
        
        return 'http://%sgeocoder.us/%s' % (auth, resource)
    
    def geocode(self, query, exactly_one=True):
        if isinstance(query, unicode):
            query = query.encode('utf-8')
        query_str = self.format_string % query
        
        page = urlopen("%s?%s" % (
            self.get_url(),
            urlencode({'address':query_str})
        ))
        
        reader = csv.reader(page)
        
        places = [r for r in reader]
        
        # GeoNames only returns the closest match, no matter what.
        #
        #if exactly_one and len(places) != 1:
        #    raise ValueError("Didn't find exactly one placemark! " \
        #                     "(Found %d.)" % len(places))
        #
        #if exactly_one:
        #    return self._parse_result(places[0])
        #else:
        #    return [self._parse_result(place) for place in places]
        
        return self._parse_result(places[0])
    
    @staticmethod
    def _parse_result(result):
        # turn x=y pairs ("lat=47.6", "long=-117.426") into dict key/value pairs:
        place = dict(
            filter(lambda x: len(x)>1, # strip off bits that aren't pairs (i.e. "geocoder modified" status string")
            map(lambda x: x.split('=', 1), result) # split the key=val strings into (key, val) tuples
        ))
        
        address = [
            place.get('number', None),
            place.get('prefix', None),
            place.get('street', None),
            place.get('type', None),
            place.get('suffix', None)
        ]
        city = place.get('city', None)
        state = place.get('state', None)
        zip_code = place.get('zip', None)
        
        name = util.join_filter(", ", [
            util.join_filter(" ", address),
            city,
            util.join_filter(" ", [state, zip_code])
        ])
        
        latitude = place.get('lat', None)
        longitude = place.get('long', None)
        if latitude and longitude:
            latlon = float(latitude), float(longitude)
        else:
            return None
        
        # TODO use Point/Location object API in 0.95
        #if latitude and longitude:
        #    point = Point(latitude, longitude)
        #else:
        #    point = None
        #return Location(name, point, dict(result))
        return name, latlon
