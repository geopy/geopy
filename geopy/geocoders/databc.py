"""
:class:`.DataBC` geocoder.
"""

from geopy.compat import urlencode

from geopy.geocoders.base import Geocoder, DEFAULT_SCHEME, DEFAULT_TIMEOUT
from geopy.exc import GeocoderQueryError
from geopy.location import Location
from geopy.util import logger


__all__ = ("DataBC", )


class DataBC(Geocoder):
    """
    Geocoder using the Physical Address Geocoder from DataBC. Documentation at:
        http://www.data.gov.bc.ca/dbc/geographic/locate/geocoding.page
    """

    def __init__(self, scheme=DEFAULT_SCHEME, timeout=DEFAULT_TIMEOUT, proxies=None, user_agent=None):
        """
        Create a DataBC-based geocoder.

        :param string scheme: Desired scheme.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.
        """
        super(DataBC, self).__init__(
            scheme=scheme, timeout=timeout, proxies=proxies, user_agent=user_agent
        )
        self.api = '%s://apps.gov.bc.ca/pub/geocoder/addresses.geojson' % self.scheme

    def geocode(
            self,
            query,
            max_results=25,
            set_back=0,
            location_descriptor='any',
            exactly_one=True,
            timeout=None,
        ):
        """
        Geocode a location query.

        :param string query: The address or query you wish to geocode.

        :param int max_results: The maximum number of resutls to request.

        :param float set_back: The distance to move the accessPoint away
            from the curb (in meters) and towards the interior of the parcel.
            location_descriptor must be set to accessPoint for set_back to
            take effect.

        :param string location_descriptor: The type of point requested. It
            can be any, accessPoint, frontDoorPoint, parcelPoint,
            rooftopPoint and routingPoint.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.
        """
        params = {'addressString': query}
        if set_back != 0:
            params['setBack'] = set_back
        if location_descriptor not in ['any',
                                       'accessPoint',
                                       'frontDoorPoint',
                                       'parcelPoint',
                                       'rooftopPoint',
                                       'routingPoint']:
            raise GeocoderQueryError(
                "You did not provided a location_descriptor "
                "the webservice can consume. It should be any, accessPoint, "
                "frontDoorPoint, parcelPoint, rooftopPoint or routingPoint."
            )
        params['locationDescriptor'] = location_descriptor
        if exactly_one is True:
            max_results = 1
        params['maxResults'] = max_results

        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        response = self._call_geocoder(url, timeout=timeout)

        # Success; convert from GeoJSON
        if not len(response['features']):
            return None
        geocoded = []
        for feature in response['features']:
            geocoded.append(self._parse_feature(feature))
        if exactly_one is True:
            return geocoded[0]
        return geocoded

    @staticmethod
    def _parse_feature(feature):
        properties = feature['properties']
        coordinates = feature['geometry']['coordinates']
        return Location(
            properties['fullAddress'], (coordinates[1], coordinates[0]),
            properties
        )
