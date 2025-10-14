import warnings
from functools import partial
from urllib.parse import urlencode

from geopy.exc import GeocoderQueryError

from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("IGNFrance", )


class IGNFrance(Geocoder):
    """Geocoder using the IGN France GeoCoder OpenLS API.

    Documentation at:
        https://geoservices.ign.fr/documentation/services/services-geoplateforme/geocodage
    """

    geocode_path = '/geocodage/search'
    reverse_path = '/geocodage/reverse'

    def __init__(
            self,
            api_key=None,
            *,
            username=None,
            password=None,
            referer=None,
            domain='data.geopf.fr',
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """

        :param str api_key: Not used.

            .. deprecated:: 2.3
                IGNFrance geocoding methods no longer accept or require
                authentication, see `<https://geoservices.ign.fr/actualites/2021-10-04-evolution-des-modalites-dacces-aux-services-web>`_.
                This parameter is scheduled for removal in geopy 3.0.

        :param str username: Not used.

            .. deprecated:: 2.3
                See the `api_key` deprecation note.

        :param str password: Not used.

            .. deprecated:: 2.3
                See the `api_key` deprecation note.

        :param str referer: Not used.

            .. deprecated:: 2.3
                See the `api_key` deprecation note.

        :param str domain: Currently it is ``'data.geopf.fr'``, can
            be changed for testing purposes.

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
        """  # noqa
        super().__init__(
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )

        if api_key or username or password or referer:
            warnings.warn(
                "IGNFrance no longer accepts or requires authentication, "
                "so api_key, username, password and referer are not used "
                "anymore. These arguments should be removed. "
                "In geopy 3 these options will be removed, causing "
                "an error instead of this warning.",
                DeprecationWarning,
                stacklevel=2,
            )

        self.domain = domain.strip('/')

        self.geocode_api = (
            '%s://%s%s' % (self.scheme, self.domain, self.geocode_path)
        )
        self.reverse_api = (
            '%s://%s%s' % (self.scheme, self.domain, self.reverse_path)
        )

    def geocode(
            self,
            query,
            *,
            query_type='address',
            limit=None,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            maximum_responses=None
    ):
        """
        Return a location point by address.

        :param str query: The query string to be geocoded.

        :param str query_type: The type to provide for geocoding. It can be
            `PositionOfInterest`, `StreetAddress` or `CadastralParcel`.
            `StreetAddress` is the default choice if none provided.

       :param int limit: Defines the maximum number of items in the
            response structure. If not provided and there are multiple
            results the IGN API will return 10 results by default.
            This will be reset to one if ``exactly_one`` is True.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

       :param int maximum_responses: alias for limit

            .. deprecated
                IGNFrance geocoding methods no longer accept or require this.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """

        # Check if acceptable query type
        updated_query_types = {'PositionOfInterest': 'poi',
                               'StreetAddress': 'address',
                               'CadastralParcel': 'parcel'}
        if query_type in updated_query_types.keys():
            query_type = updated_query_types[query_type]
        if query_type not in list(updated_query_types.values()):
            raise GeocoderQueryError("""You did not provide a query_type the
            webservice can consume. It should be poi, address, parcel (new api),
            PositionOfInterest, StreetAddress or CadastralParcel (deprecated)""")

        # Check query validity for CadastralParcel
        if query_type == 'parcel' and len(query.strip()) != 14:
            raise GeocoderQueryError("""You must send a string of fourteen
                characters long to match the cadastre required code""")

        # Deal with maximum_responses as an alias for limit
        if limit is None:
            limit = maximum_responses

        params = {
            'q': query,
            'index': query_type,
        }

        if limit is None:
            limit = maximum_responses
        if limit is not None:
            params['limit'] = limit

        url = "?".join((self.geocode_api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def reverse(
            self,
            query,
            *,
            reverse_geocode_preference=('StreetAddress', ),
            limit=None,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL,
            maximum_responses=None
    ):
        """
        Return an address by location point.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

       :param int limit: Defines the maximum number of items in the
            response structure. If not provided and there are multiple
            results the IGN API will return 10 results by default.
            This will be reset to one if ``exactly_one`` is True.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

       :param int maximum_responses: alias for limit

            .. deprecated
                IGNFrance geocoding methods no longer accept or require this.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """

        try:
            lat, lon = self._coerce_point_to_string(query).split(',')
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")

        params = {
            'lat': lat,
            'lon': lon,
        }

        url = "?".join((self.reverse_api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_feature(self, feature):
        # Parse each resource.
        latitude = feature.get('geometry', {}).get('coordinates', [])[1]
        longitude = feature.get('geometry', {}).get('coordinates', [])[0]
        placename = feature.get('properties', {}).get('label')

        return Location(placename, (latitude, longitude), feature)

    def _parse_json(self, response, exactly_one):
        if response is None or 'features' not in response:
            return None
        features = response['features']
        if not len(features):
            return None
        if exactly_one:
            return self._parse_feature(features[0])
        else:
            return [self._parse_feature(feature) for feature in features]
