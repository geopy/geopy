from functools import partial
from urllib.parse import urlencode

from geopy.exc import GeocoderQueryError
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("DataBC", )


class DataBC(Geocoder):
    """Geocoder using the Physical Address Geocoder from DataBC.

    Documentation at:
        http://www.data.gov.bc.ca/dbc/geographic/locate/geocoding.page
    """

    geocode_path = '/pub/geocoder/addresses.geojson'

    def __init__(
            self,
            *,
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`.

        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str user_agent:
            See :attr:`geopy.geocoders.options.default_user_agent`.

        :type ssl_context: :class:`ssl.SSLContext`
        :param ssl_context:
            See :attr:`geopy.geocoders.options.default_ssl_context`.

        :param callable adapter_factory:
            See :attr:`geopy.geocoders.options.default_adapter_factory`.

            .. versionadded:: 2.0
        """
        super().__init__(
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )
        domain = 'apps.gov.bc.ca'
        self.api = '%s://%s%s' % (self.scheme, domain, self.geocode_path)

    def geocode(
            self,
            query,
            *,
            max_results=25,
            set_back=0,
            location_descriptor='any',
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return a location point by address.

        :param str query: The address or query you wish to geocode.

        :param int max_results: The maximum number of resutls to request.

        :param float set_back: The distance to move the accessPoint away
            from the curb (in meters) and towards the interior of the parcel.
            location_descriptor must be set to accessPoint for set_back to
            take effect.

        :param str location_descriptor: The type of point requested. It
            can be any, accessPoint, frontDoorPoint, parcelPoint,
            rooftopPoint and routingPoint.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
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
        if exactly_one:
            max_results = 1
        params['maxResults'] = max_results

        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_json(self, response, exactly_one):
        # Success; convert from GeoJSON
        if not len(response['features']):
            return None
        geocoded = []
        for feature in response['features']:
            geocoded.append(self._parse_feature(feature))
        if exactly_one:
            return geocoded[0]
        return geocoded

    def _parse_feature(self, feature):
        properties = feature['properties']
        coordinates = feature['geometry']['coordinates']
        return Location(
            properties['fullAddress'], (coordinates[1], coordinates[0]),
            properties
        )
