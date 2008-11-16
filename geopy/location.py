from geopy.point import Point

class Location(object):
    def __init__(self, name="", point=None, attributes=None, **kwargs):
        self.name = name
        if point is not None:
            self.point = Point(point)
        if attributes is None:
            attributes = {}
        self.attributes = dict(attributes, **kwargs)
    
    def __getitem__(self, index):
        """Backwards compatibility with geopy 0.93 tuples."""
        return (self.name, self.point)[index]
    
    def __repr__(self):
        return "Location(%r, %r)" % (self.name, self.point)
    
    def __iter__(self):
        return iter((self.name, self.point))
    
    def __eq__(self, other):
        return (self.name, self.point) == (other.name, other.point)
    
    def __ne__(self, other):
        return (self.name, self.point) != (other.name, other.point)
    