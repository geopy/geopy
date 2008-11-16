import getpass
import xmlrpclib
from geopy.geocoders.base import Geocoder
from geopy.point import Point
from geopy.location import Location
from geopy import util

class GeocoderDotUS(Geocoder):
    def __init__(self, username=None, password=None, format_string='%s'):
        super(GeocoderDotUS, self).__init__(format_string=format_string)
        
        if username and password is None:
            password = getpass.getpass(
                "geocoder.us password for %r: " % username
            )
        
        self.username = username
        self.__password = password
    
    def get_url(self, string=None):
        username = self.username
        password = self.__password
        if username and password:
            auth = '%s@%s:' % (username, password)
            resource = 'member/service/xmlrpc/'
        else:
            auth = ''
            resource = 'service/xmlrpc/'
        
        return 'http://%sgeocoder.us/%s' % (auth, resource)
    
    def geocode(self, string, **kwargs):
        locations = []
        server = xmlrpclib.ServerProxy(self.url)
        results = server.geocode(self.format_string % string)
        for result in results:
            name = self._format_name(result)
            latitude = result.get('lat')
            longitude = result.get('long')
            if latitude and longitude:
                point = Point(latitude, longitude)
            else:
                point = None
            location = Location(name, point, dict(result))
            locations.append(location)
        return locations
    
    def _format_name(self, result):
        address = [
            result.get('number'),
            result.get('prefix'),
            result.get('street'),
            result.get('street_type'),
            result.get('suffix')
        ]
        city = result.get('city')
        state = result.get('state')
        zip_code = result.get('zip')
        
        return util.join_filter(", ", [
            util.join_filter(" ", address),
            city,
            util.join_filter(" ", [state, zip_code])
        ])
