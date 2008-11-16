class Geocoder(object):
    def __init__(self, format_string='%s'):
        self.format_string = format_string

    def geocode(self, location):
        raise NotImplementedError

    def reverse(self, point):
        raise NotImplementedError

    def geocode_one(self, location):
        results = self.geocode(location)
        first = None
        for result in results:
            if first is None:
                first = result
            else:
                raise GeocoderResultError("Geocoder returned more than one result!")
        if first is not None:
            return first
        else:
            raise GeocoderResultError("Geocoder returned no results!")

    def geocode_first(self, location):
        results = self.geocode(location)
        for result in results:
            return result
        return None

class GeocoderError(Exception):
    pass

class GeocoderResultError(GeocoderError):
    pass
