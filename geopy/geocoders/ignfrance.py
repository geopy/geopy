import base64
import xml.etree.ElementTree as ET
from functools import partial
from urllib.parse import urlencode

from geopy.exc import ConfigurationError, GeocoderQueryError
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location
from geopy.util import logger

__all__ = ("IGNFrance", )


class IGNFrance(Geocoder):
    """Geocoder using the IGN France GeoCoder OpenLS API.

    Documentation at:
        https://geoservices.ign.fr/documentation/geoservices/index.html
    """

    xml_request = """<?xml version="1.0" encoding="UTF-8"?>
    <XLS version="1.2"
        xmlns="http://www.opengis.net/xls"
        xmlns:gml="http://www.opengis.net/gml"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.opengis.net/xls
        http://schemas.opengis.net/ols/1.2/olsAll.xsd">
        <RequestHeader srsName="epsg:4326"/>
        <Request methodName="{method_name}"
                 maximumResponses="{maximum_responses}"
                 requestID=""
                 version="1.2">
            {sub_request}
        </Request>
    </XLS>"""

    api_path = '/%(api_key)s/geoportail/ols'

    def __init__(
            self,
            api_key,
            *,
            username=None,
            password=None,
            referer=None,
            domain='wxs.ign.fr',
            scheme=None,
            timeout=DEFAULT_SENTINEL,
            proxies=DEFAULT_SENTINEL,
            user_agent=None,
            ssl_context=DEFAULT_SENTINEL,
            adapter_factory=None
    ):
        """

        :param str api_key: The API key required by IGN France API
            to perform geocoding requests. You can get your key here:
            https://geoservices.ign.fr/documentation/services-acces.html.
            Mandatory. For authentication with referer
            and with username/password, the api key always differ.

        :param str username: When making a call need HTTP simple
            authentication username. Mandatory if no referer set

        :param str password: When making a call need HTTP simple
            authentication password. Mandatory if no referer set

        :param str referer: When making a call need HTTP referer.
            Mandatory if no password and username

        :param str domain: Currently it is ``'wxs.ign.fr'``, can
            be changed for testing purposes for developer API
            e.g ``'gpp3-wxs.ign.fr'`` at the moment.

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

        # Catch if no api key with username and password
        # or no api key with referer
        if not ((api_key and username and password) or (api_key and referer)):
            raise ConfigurationError('You should provide an api key and a '
                                     'username with a password or an api '
                                     'key with a referer depending on '
                                     'created api key')
        if (username and password) and referer:
            raise ConfigurationError('You can\'t set username/password and '
                                     'referer together. The API key always '
                                     'differs depending on both scenarios')
        if username and not password:
            raise ConfigurationError(
                'username and password must be set together'
            )

        self.api_key = api_key
        self.username = username
        self.password = password
        self.referer = referer
        self.domain = domain.strip('/')
        api_path = self.api_path % dict(api_key=self.api_key)
        self.api = '%s://%s%s' % (self.scheme, self.domain, api_path)

    def geocode(
            self,
            query,
            *,
            query_type='StreetAddress',
            maximum_responses=25,
            is_freeform=False,
            filtering=None,
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return a location point by address.

        :param str query: The query string to be geocoded.

        :param str query_type: The type to provide for geocoding. It can be
            `PositionOfInterest`, `StreetAddress` or `CadastralParcel`.
            `StreetAddress` is the default choice if none provided.

        :param int maximum_responses: The maximum number of responses
            to ask to the API in the query body.

        :param str is_freeform: Set if return is structured with
            freeform structure or a more structured returned.
            By default, value is False.

        :param str filtering: Provide string that help setting geocoder
            filter. It contains an XML string. See examples in documentation
            and ignfrance.py file in directory tests.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """

        # Check if acceptable query type
        if query_type not in ['PositionOfInterest',
                              'StreetAddress',
                              'CadastralParcel']:
            raise GeocoderQueryError("""You did not provided a query_type the
            webservice can consume. It should be PositionOfInterest,
            'StreetAddress or CadastralParcel""")

        # Check query validity for CadastralParcel
        if query_type == 'CadastralParcel' and len(query.strip()) != 14:
            raise GeocoderQueryError("""You must send a string of fourteen
                characters long to match the cadastre required code""")

        sub_request = """
                <GeocodeRequest returnFreeForm="{is_freeform}">
                    <Address countryCode="{query_type}">
                        <freeFormAddress>{query}</freeFormAddress>
                        {filtering}
                    </Address>
                </GeocodeRequest>
        """

        xml_request = self.xml_request.format(
            method_name='LocationUtilityService',
            sub_request=sub_request,
            maximum_responses=maximum_responses
        )

        # Manage type change for xml case sensitive
        if is_freeform:
            is_freeform = 'true'
        else:
            is_freeform = 'false'

        # Manage filtering value
        if filtering is None:
            filtering = ''

        # Create query using parameters
        request_string = xml_request.format(
            is_freeform=is_freeform,
            query=query,
            query_type=query_type,
            filtering=filtering
        )

        params = {
            'xls': request_string
        }

        url = "?".join((self.api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = partial(
            self._parse_xml, is_freeform=is_freeform, exactly_one=exactly_one
        )
        return self._request_raw_content(url, callback, timeout=timeout)

    def reverse(
            self,
            query,
            *,
            reverse_geocode_preference=('StreetAddress', ),
            maximum_responses=25,
            filtering='',
            exactly_one=True,
            timeout=DEFAULT_SENTINEL
    ):
        """
        Return an address by location point.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of ``(latitude,
            longitude)``, or string as ``"%(latitude)s, %(longitude)s"``.

        :param list reverse_geocode_preference: Enable to set expected results
            type. It can be `StreetAddress` or `PositionOfInterest`.
            Default is set to `StreetAddress`.

        :param int maximum_responses: The maximum number of responses
            to ask to the API in the query body.

        :param str filtering: Provide string that help setting geocoder
            filter. It contains an XML string. See examples in documentation
            and ignfrance.py file in directory tests.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :rtype: ``None``, :class:`geopy.location.Location` or a list of them, if
            ``exactly_one=False``.

        """

        sub_request = """
            <ReverseGeocodeRequest>
                {reverse_geocode_preference}
                <Position>
                  <gml:Point>
                    <gml:pos>{query}</gml:pos>
                  </gml:Point>
                  {filtering}
                </Position>
            </ReverseGeocodeRequest>
        """

        xml_request = self.xml_request.format(
            method_name='ReverseGeocodeRequest',
            sub_request=sub_request,
            maximum_responses=maximum_responses
        )

        for pref in reverse_geocode_preference:
            if pref not in ('StreetAddress', 'PositionOfInterest'):
                raise GeocoderQueryError(
                    '`reverse_geocode_preference` must contain '
                    'one or more of: StreetAddress, PositionOfInterest'
                )

        point = self._coerce_point_to_string(query, "%(lat)s %(lon)s")
        reverse_geocode_preference = '\n'.join((
            '<ReverseGeocodePreference>%s</ReverseGeocodePreference>' % pref
            for pref
            in reverse_geocode_preference
        ))

        request_string = xml_request.format(
            maximum_responses=maximum_responses,
            query=point,
            reverse_geocode_preference=reverse_geocode_preference,
            filtering=filtering
        )

        url = "?".join((self.api, urlencode({'xls': request_string})))

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        callback = partial(
            self._parse_xml,
            exactly_one=exactly_one,
            is_reverse=True,
            is_freeform='false'
        )
        return self._request_raw_content(url, callback, timeout=timeout)

    def _parse_xml(self,
                   page,
                   is_reverse=False,
                   is_freeform=False,
                   exactly_one=True):
        """
        Returns location, (latitude, longitude) from XML feed
        and transform to json
        """
        # Parse the page
        tree = ET.fromstring(page.encode('utf-8'))

        # Clean tree from namespace to facilitate XML manipulation
        def remove_namespace(doc, namespace):
            """Remove namespace in the document in place."""
            ns = '{%s}' % namespace
            nsl = len(ns)
            for elem in doc.iter():
                if elem.tag.startswith(ns):
                    elem.tag = elem.tag[nsl:]

        remove_namespace(tree, 'http://www.opengis.net/gml')
        remove_namespace(tree, 'http://www.opengis.net/xls')
        remove_namespace(tree, 'http://www.opengis.net/xlsext')

        # Return places as json instead of XML
        places = self._xml_to_json_places(tree, is_reverse=is_reverse)

        if not places:
            return None
        if exactly_one:
            return self._parse_place(places[0], is_freeform=is_freeform)
        else:
            return [
                self._parse_place(
                    place,
                    is_freeform=is_freeform
                ) for place in places
            ]

    def _xml_to_json_places(self, tree, is_reverse=False):
        """
        Transform the xml ElementTree due to XML webservice return to json
        """

        select_multi = (
            'GeocodedAddress'
            if not is_reverse
            else 'ReverseGeocodedLocation'
        )

        adresses = tree.findall('.//' + select_multi)
        places = []

        sel_pl = './/Address/Place[@type="{}"]'
        for adr in adresses:
            el = {}
            el['pos'] = adr.find('./Point/pos')
            el['street'] = adr.find('.//Address/StreetAddress/Street')
            el['freeformaddress'] = adr.find('.//Address/freeFormAddress')
            el['municipality'] = adr.find(sel_pl.format('Municipality'))
            el['numero'] = adr.find(sel_pl.format('Numero'))
            el['feuille'] = adr.find(sel_pl.format('Feuille'))
            el['section'] = adr.find(sel_pl.format('Section'))
            el['departement'] = adr.find(sel_pl.format('Departement'))
            el['commune_absorbee'] = adr.find(sel_pl.format('CommuneAbsorbee'))
            el['commune'] = adr.find(sel_pl.format('Commune'))
            el['insee'] = adr.find(sel_pl.format('INSEE'))
            el['qualite'] = adr.find(sel_pl.format('Qualite'))
            el['territoire'] = adr.find(sel_pl.format('Territoire'))
            el['id'] = adr.find(sel_pl.format('ID'))
            el['id_tr'] = adr.find(sel_pl.format('ID_TR'))
            el['bbox'] = adr.find(sel_pl.format('Bbox'))
            el['nature'] = adr.find(sel_pl.format('Nature'))
            el['postal_code'] = adr.find('.//Address/PostalCode')
            el['extended_geocode_match_code'] = adr.find(
                './/ExtendedGeocodeMatchCode'
            )

            place = {}

            def testContentAttrib(selector, key):
                """
                Helper to select by attribute and if not attribute,
                value set to empty string
                """
                return selector.attrib.get(
                    key,
                    None
                ) if selector is not None else None

            place['accuracy'] = testContentAttrib(
                adr.find('.//GeocodeMatchCode'), 'accuracy')

            place['match_type'] = testContentAttrib(
                adr.find('.//GeocodeMatchCode'), 'matchType')

            place['building'] = testContentAttrib(
                adr.find('.//Address/StreetAddress/Building'), 'number')

            place['search_centre_distance'] = testContentAttrib(
                adr.find('.//SearchCentreDistance'), 'value')

            for key, value in iter(el.items()):
                if value is not None:
                    place[key] = value.text
                else:
                    place[key] = None

            # We check if lat lng is not empty and unpack accordingly
            if place['pos']:
                lat, lng = place['pos'].split(' ')
                place['lat'] = lat.strip()
                place['lng'] = lng.strip()
            else:
                place['lat'] = place['lng'] = None

            # We removed the unused key
            place.pop("pos", None)
            places.append(place)

        return places

    def _request_raw_content(self, url, callback, *, timeout):
        """
        Send the request to get raw content.
        """
        headers = {}
        if self.referer is not None:
            headers['Referer'] = self.referer

        if self.username and self.password and self.referer is None:
            credentials = '{0}:{1}'.format(self.username, self.password).encode()
            auth_str = base64.standard_b64encode(credentials).decode()
            headers['Authorization'] = 'Basic {}'.format(auth_str.strip())

        return self._call_geocoder(
            url,
            callback,
            headers=headers,
            timeout=timeout,
            is_json=False,
        )

    def _parse_place(self, place, is_freeform=None):
        """
        Get the location, lat, lng and place from a single json place.
        """
        # When freeform already so full address
        if is_freeform == 'true':
            location = place.get('freeformaddress')
        else:
            # For parcelle
            if place.get('numero'):
                location = place.get('street')
            else:
                # When classic geocoding
                # or when reverse geocoding
                location = "%s %s" % (
                    place.get('postal_code', ''),
                    place.get('commune', ''),
                )
                if place.get('street'):
                    location = "%s, %s" % (
                        place.get('street', ''),
                        location,
                    )
                if place.get('building'):
                    location = "%s %s" % (
                        place.get('building', ''),
                        location,
                    )

        return Location(location, (place.get('lat'), place.get('lng')), place)
