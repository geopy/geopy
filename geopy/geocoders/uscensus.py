from functools import partial
from urllib.parse import urlencode

from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.point import Point
from geopy.util import logger

__all__ = ("USCensus", )


class USCensus(Geocoder):
    """ Geocoder that uses the United States Census Bureau geocode API

    Documentation at:
        https://geocoding.geo.census.gov/geocoder
    """

    structured_query_params = {
        'street',
        'city',
        'state',
        'zip',
    }

    def __init__(
        self,
        *,
        timeout=DEFAULT_SENTINEL,
        proxies=DEFAULT_SENTINEL,
        domain='geocoding.geo.census.gov',
        scheme=None,
        user_agent=None,
        ssl_context=DEFAULT_SENTINEL,
        adapter_factory=None
    ):
        """
        :param int timeout:
            See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies:
            See :attr:`geopy.geocoders.options.default_proxies`.

        :param str domain: Domain where the target US Census geocoder service
            is hosted.

        :param str scheme:
            See :attr:`geopy.geocoders.options.default_scheme`.

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
            adapter_factory=adapter_factory
        )
        self.api = f"{self.scheme}://{domain}/geocoder"

    def geocode(
        self,
        query,
        *,
        dataset_type='Public_AR',
        spatial_benchmark='Current',
        geolookup=False,
        geography_vintage='Current',
        layers=None,
        exactly_one=True,
        timeout=16
    ):
        """
        Return a location point by address.

        :param query: The address, query or structured query, you wish to geocode.
            For a structured query, provide a dictionary whose keys
            are: `street`, `city`, `state`, and `zip`.

        :type query: dict or str

        :param dataset_type: Data set type that will be used for a given query.

        :param spatial_benchmark: The spatial benchmark that will be used for the query.
            The same spatial benchmark will be used for the query and for geolookup if
            a geolookup is performed.

        :param geolookup: Specifies whether a given query will perform a geolookup.
            If set to True, a geolookup will be performed as part of the query and
            additional geography data will be added to the raw
            :class:`geopy.location.Location`.

        :param geography_vintage: Specifies what vintage of geography is will be used
            for a geoLookup.

        :param layers: Specifies which TigerWeb WMS layers to include in
            geoLookup geography output. Layers can be specified as a comma-separate
            :class:`str` or as a :class:`collections.abs.Sequence`.

        :type layers: str or :class:`collections.abs.Sequence`

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location`, or a list of
            :class:`geopy.location.Location` if ``exactly_one=False``.

        """
        params = {}
        if isinstance(query, str):
            search_type = 'onelineaddress'
            params['address'] = query
        else:
            search_type = 'address'
            params = self._filter_params(query, self.structured_query_params)
        params['benchmark'] = f"{dataset_type}_{spatial_benchmark}"
        params['format'] = 'json'
        if geolookup:
            return_type = 'geographies'
            params['vintage'] = f"{geography_vintage}_{spatial_benchmark}"
            if layers:
                if isinstance(layers, str):
                    params['layers'] = layers
                else:
                    params['layers'] = ','.join(layers)
        else:
            return_type = 'locations'
        url = f"{self.api}/{return_type}/{search_type}?{urlencode(params)}"
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(self._parse_json, exactly_one=exactly_one)
        return self._call_geocoder(url, callback, timeout=timeout)

    @staticmethod
    def _filter_params(params, allowed_params):
        """
        Returns a dict of filtered parameters containing allowed parameters.

        :param params: Parameters that will be filtered.
        :param allowed_params: A set of keys that will be used to filter params. A new
            dictionary will be returned that contains only the items whose keys
            are in allowed_params.
        """
        return {key: val for key, val in params.items() if key in allowed_params}

    @staticmethod
    def _parse_address_match(address_match):
        """
        Helper method to parse a geopy Location from a matched address JSON field.

        :param address_match: A matched address JSON field from which to parse a geopy
            Location.
        """
        coordinates = address_match['coordinates']
        point = Point(latitude=coordinates['y'], longitude=coordinates['x'])
        return Location(address_match['matchedAddress'], point, address_match)

    @staticmethod
    def _parse_json(json_data, exactly_one):
        """
        Helper method to parse a US Census geocode API JSON response

        :param json_data: JSON data from US Census geocode API
        :param exactly_one: Indicates whether to return only the first matched address
            in the case that JSON data contains multiple matched address.
        """
        result = json_data['result']
        address_matches = result['addressMatches']
        if not address_matches:
            return None
        if exactly_one:
            return USCensus._parse_address_match(address_matches[0])
        else:
            return [USCensus._parse_address_match(match) for match in address_matches]
