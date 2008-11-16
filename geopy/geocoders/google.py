import urllib
import simplejson
from geopy.geocoders.base import Geocoder
from geopy import Point, Location

class Google(Geocoder):
    def __init__(self, key, output='xml', *args, **kwargs):
        super(Google, self).__init__(*args, **kwargs)
        self.key = key
        self.output = output
    
    @property
    def url(self):
        params = {
            'q': 
        }
        return 'http://maps.google.com/maps/geo?'q=1600+Amphitheatre+Parkway,+Mountain+View,+CA&output=xml&key=abcdefg
    
    def geocode(self, string, **kwargs):
        