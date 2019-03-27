# -*- coding: utf-8 -*-
# Copyright (C) 2018 HeiGIT, University of Heidelberg.
#
# Modifications Copyright (C) 2018 HeiGIT, University of Heidelberg.
#
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#

import warnings

from geopy.compat import urlencode
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

"""Performs requests to the ORS geocode API (direct Pelias clone)."""

__all__ = ("openrouteservice",)

_DEFAULT_OPENROUTESERVICE_DOMAIN = 'api.openrouteservice.org'


class openrouteservice(Geocoder):
    """openrouteservice geocoder.

    Documentation at:
        https://github.com/GIScience/openrouteservice-py/blob/master/openrouteservice/geocode.py

    # TODO!
    .. versionchanged::

    """

    geocode_path = '/geocode/search'
    reverse_path = '/geocode/reverse'

    def __init__(self,
                 api_key,
                 timeout=DEFAULT_SENTINEL,
                 proxies=DEFAULT_SENTINEL,
                 scheme=None,
                 format_string=None,
                 user_agent=None,
                 ssl_context=DEFAULT_SENTINEL,
                 domain=_DEFAULT_OPENROUTESERVICE_DOMAIN,
                 ):
        """
        :param str api_key: openrouteservice API key. Please visit https://openrouteservice.org/sign-up to create one.

        :param int timeout: See :attr:`geopy.geocoders.options.default_timeout`.

        :param dict proxies: See :attr:`geopy.geocoders.options.default_proxies`.

        :param str scheme: See :attr:`geopy.geocoders.options.default_scheme`.

        :param str format_string: See :attr:`geopy.geocoders.options.default_format_string`.

        :param str user_agent: See :attr:`geopy.geocoders.options.default_user_agent`.

        :param ssl_context: See :attr:`geopy.geocoders.options.default_ssl_context`.
        :type ssl_context: :class:`ssl.SSLContext`

        :param domain: Default openrouteservice domain.
        """
        super(openrouteservice, self).__init__(
            format_string=format_string,
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context
        )
        self.api_key = api_key
        self.domain = domain.strip('/')

        self.geocode_api = "%s://%s%s" % (self.scheme, self.domain, self.geocode_path)
        self.reverse_api = "%s://%s%s" % (self.scheme, self.domain, self.reverse_path)

    def _generate_auth_url(self, path, params):
        """
        Returns the path and query string portion of the request URL.

        :param path: The path portion of the URL. Geocode search or reverse.
        :type path:

        :param params: URL parameters.
        :type params: dict or list of key/value tuples

        :rtype: string
        """
        if type(params) is dict:
            params = sorted(dict(**params).items())

        return "?".join((path, urlencode(params)))

    def geocode(self,
                query,
                exactly_one=True,
                timeout=DEFAULT_SENTINEL,
                boundary_rect=None,
                focus_point=None,
                circle_point=None,
                circle_radius=None,
                country=None,
                layers=None,
                sources=None,
                size=None
                ):
        """
        Geocoding is the process of converting addresses into geographic
        coordinates.
        This endpoint queries directly against a Pelias instance.

        :param query: Full-text query against search endpoint. Required.
        :type query: string

        :param exactly_one: Return one result or a list of results.
        :type exactly_one: boolean

        :param timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.
        :type timeout: integer

        :param boundary_rect: Coordinates to restrict search within.
            Example: ``[Point(22, 180), Point(-22, -180)]``.
            .. versionchanged:: 1.17.0
                Previously boundary_rect could be a list of 4 strings or numbers
                in the format of ``[longitude, latitude, longitude, latitude]``.
                This format is now deprecated in favor of a list/tuple
                of a pair of geopy Points and will be removed in geopy 2.0.
        :type boundary_rect: list or tuple of 2 items of :class:`geopy.point.Point`
            or ``(latitude, longitude)`` or ``"%(latitude)s, %(longitude)s"``.

        :param focus_point: Focusses the search to be around this point and gives
            results within a 100 km radius higher scores.
        :type query: list or tuple of (Long, Lat)

        :param circle_point: Geographical constraint in form a circle.
        :type circle_point: list or tuple of (Long, Lat)

        :param circle_radius: Radius of circle constraint in km. Default 50.
        :type circle_radius: integer

        :param sources: The originating source of the data. One or more of
            ['osm', 'oa', 'wof', 'gn']. Currently only 'osm', 'wof' and 'gn' are
            supported.
        :type sources: list of strings

        :param layers: The administrative hierarchy level for the query. Refer to
            https://github.com/pelias/documentation/blob/master/search.md#filter-by-data-type
            for details.
        :type layers: list of strings

        :param country: Constrain query by country. Accepts a alpha-2 or alpha-3
            digit ISO-3166 country code.
        :type country: string

        :param size: The amount of results returned. Default 10.
        :type size: integer

        :raises ValueError: When parameter has invalid value(s).
        :raises TypeError: When parameter is of the wrong type.
        :raises AttributeError: When requested parameter is not provided.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """

        if self.domain == _DEFAULT_OPENROUTESERVICE_DOMAIN and self.api_key is None:
            raise TypeError(
                "No API key was specified. Please visit https://openrouteservice.org/sign-up to create one.")

        params = {'text': query}

        if self.api_key:
            params.update({
                'api_key': self.api_key
            })

        if exactly_one:
            params['exactly_one'] = exactly_one

        if boundary_rect:
            boundary_rect = boundary_rect
            if len(boundary_rect) == 4:
                warnings.warn(
                    '%s `boundary_rect` format of '
                    '`[longitude, latitude, longitude, latitude]` is now '
                    'deprecated and will be not supported in geopy 2.0. '
                    'Use `[Point(latitude, longitude), Point(latitude, longitude)]` '
                    'instead.' % type(self).__name__,
                    DeprecationWarning,
                    stacklevel=2
                )
                lon1, lat1, lon2, lat2 = boundary_rect
                boundary_rect = [[lat1, lon1], [lat2, lon2]]
            lon1, lat1, lon2, lat2 = self._format_bounding_box(
                boundary_rect, "%(lon1)s,%(lat1)s,%(lon2)s,%(lat2)s").split(',')
            params['boundary.rect.min_lon'] = lon1
            params['boundary.rect.min_lat'] = lat1
            params['boundary.rect.max_lon'] = lon2
            params['boundary.rect.max_lat'] = lat2

        if focus_point:
            try:
                focus_lat, focus_lon = self._coerce_point_to_string(focus_point).split(',')
            except ValueError:
                raise ValueError("Must be a coordinate pair or Point")
            params['focus.point.lat'] = focus_lat
            params['focus.point.lon'] = focus_lon

        if circle_point and circle_radius:
            try:
                circle_lat, circle_lon = self._coerce_point_to_string(circle_point).split(',')
            except ValueError:
                raise ValueError("Must be a coordinate pair or Point")
            params['boundary.circle.lat'] = circle_lat
            params['boundary.circle.lon'] = circle_lon
        if circle_point and not circle_radius:
            raise AttributeError("Parameter 'circle_radius' must be set.")

        if circle_radius and circle_point:
            params['boundary.circle.radius'] = circle_radius
        if circle_radius and not circle_point:
            raise AttributeError("Parameter 'circle_point' must be set.")

        if country:
            params['boundary.country'] = country

        if layers:
            try:
                params['layers'] = ",".join(map(str, layers))
            except Exception:
                raise TypeError("Expected a list or tuple, "
                                "but got {}".format(type(sources).__name__))

        if sources:
            try:
                params['sources'] = ",".join(map(str, sources))
            except Exception:
                raise TypeError("Expected a list or tuple, "
                                "but got {}".format(type(sources).__name__))

        if size and exactly_one is False:
            params['size'] = size
        if size is not None and size > 1 and exactly_one is True:
            raise AttributeError("Parameter 'exactly_one' must be set False.")

        url = self._generate_auth_url(self.geocode_api, params)

        logger.debug("%s.geocode.search: %s", self.__class__.__name__, url)

        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    def reverse(self,
                query,
                exactly_one=True,
                timeout=DEFAULT_SENTINEL,
                circle_radius=None,
                country=None,
                layers=None,
                sources=None,
                size=None
                ):
        """
        Reverse geocoding is the process of converting geographic coordinates into a
        human-readable address.
        This endpoint queries directly against a Pelias instance.

        :param query: Coordinate tuple. Required.
        :type query: string

        :param exactly_one: Return one result or a list of results. Default: True.
        :type exactly_one: boolean

        :param timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.
        :type timeout: integer

        :param circle_radius: Radius around point to limit query in km. Default 1.
        :type circle_radius: integer

        :param sources: The originating source of the data. One or more of
            ['osm', 'oa', 'wof', 'gn']. Currently only 'osm', 'wof' and 'gn' are
            supported.
        :type sources: list of strings

        :param country: Constrain query by country. Accepts a alpha-2 or alpha-3
            digit ISO-3166 country codes.
        :type country: string

        :param layers: The administrative hierarchy level for the query. Refer to
            https://github.com/pelias/documentation/blob/master/search.md#filter-by-data-type
            for details.
        :type layers: list of strings

        :param size: The amount of results returned. Default 10.
        :type size: integer

        :raises ValueError: When parameter has invalid value(s).
        :raises TypeError: When parameter is of the wrong type.
        :raises AttributeError: When requested parameter is not provided.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.
        """

        if self.domain == _DEFAULT_OPENROUTESERVICE_DOMAIN and self.api_key is None:
            raise TypeError(
                "No API key was specified. Please visit https://openrouteservice.org/sign-up to create one.")

        try:
            lat, lon = self._coerce_point_to_string(query).split(',')
        except ValueError:
            raise ValueError("Must be a coordinate pair or Point")
        params = {
            'point.lat': lat,
            'point.lon': lon,
        }

        if self.api_key:
            params.update({
                'api_key': self.api_key
            })

        if exactly_one:
            params['exactly_one'] = exactly_one

        if circle_radius and exactly_one is False:
            params['boundary.circle.radius'] = str(circle_radius)
        if circle_radius and exactly_one is True:
            raise AttributeError("Parameter 'exactly_one' must be set False.")

        if country:
            params['boundary.country'] = country

        if layers:
            try:
                params['layers'] = ",".join(map(str, layers))
            except Exception:
                raise TypeError("Expected a list or tuple, "
                                "but got {}".format(type(sources).__name__))

        if sources:
            try:
                params['sources'] = ",".join(map(str, sources))
            except Exception:
                raise TypeError("Expected a list or tuple, "
                                "but got {}".format(type(sources).__name__))

        if size and exactly_one is False:
            params['size'] = size
        if size is not None and size > 1 and exactly_one is True:
            raise AttributeError("Parameter 'exactly_one' must be set False.")

        url = "?".join((self.reverse_api, urlencode(params)))

        logger.debug("%s.geocode.reverse: %s", self.__class__.__name__, url)

        return self._parse_json(
            self._call_geocoder(url, timeout=timeout), exactly_one
        )

    @staticmethod
    def _parse_json(response, exactly_one):
        features = response['features']
        if response is None or not len(features):
            return None

        def parse_code(feature):
            latitude = feature.get('geometry', {}).get('coordinates', [])[1]
            longitude = feature.get('geometry', {}).get('coordinates', [])[0]
            placename = feature.get('properties', {}).get('name')
            return Location(placename, (latitude, longitude), feature)

        if exactly_one:
            return parse_code(features[0])
        else:
            return [parse_code(feature) for feature in features]
