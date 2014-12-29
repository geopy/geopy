"""
:class:`.IGNFrance` is the IGN France Geocoder.
"""

import xml.etree.ElementTree as ET

from geopy.compat import (urlencode, HTTPPasswordMgrWithDefaultRealm,
                          HTTPBasicAuthHandler, build_opener, u,
                          install_opener, iteritems, Request)
from geopy.geocoders.base import Geocoder, DEFAULT_TIMEOUT, DEFAULT_SCHEME
from geopy.exc import (
    GeocoderQueryError,
    ConfigurationError,
)
from geopy.location import Location
from geopy.util import logger

__all__ = ("IGNFrance", )

class IGNFrance(Geocoder):
    """
    Geocoder using the IGN France GeoCoder OpenLS API. Documentation at:
        http://api.ign.fr/tech-docs-js/fr/developpeur/search.html
    """

    def __init__(
            self,
            api_key,
            username=None,
            password=None,
            referer=None,
            domain='wxs.ign.fr',
            scheme=DEFAULT_SCHEME,
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
    ):  # pylint: disable=R0913
        """
        Initialize a customized IGN France geocoder.

        :param string api_key: The API key required by IGN France API
            to perform geocoding requests. You can get your key here:
            http://api.ign.fr. Mandatory. For authentication with referer
            and with username/password, the api key always differ.

        :param string username: When making a call need HTTP simple
            authentication username. Mandatory if no referer set

        :param string password: When making a call need HTTP simple
            authentication password. Mandatory if no referer set

        :param string referer: When making a call need HTTP referer.
            Mandatory if no password and username

        :param string domain: Currently it is 'wxs.ign.fr', can
            be changed for testing purposes for developer API
            e.g gpp3-wxs.ign.fr at the moment.

        :param string scheme: Use 'https' or 'http' as the API URL's scheme.
            Default is https. Note that SSL connections' certificates are not
            verified.

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

        """
        super(IGNFrance, self).__init__(
            scheme=scheme, timeout=timeout, proxies=proxies
        )

        # Catch if no api key  with username and password
        # or no api key with referer
        if not (api_key and password and username) \
            and not (api_key and referer):
            raise ConfigurationError('You should provide an api key and a '
                                     'username with a password or an api '
                                     'key with a referer depending on '
                                     'created api key')
        if password and username and referer:
            raise ConfigurationError('You can\'t set username/password and '
                                     'referer together. The API key always '
                                     'differs depending on both scenarios')

        self.api_key = api_key
        self.username = username
        self.password = password
        self.referer = referer
        self.domain = domain.strip('/')
        self.api = "{scheme}://{domain}/{api_key}/geoportail/ols".format(
            scheme=self.scheme,
            api_key=self.api_key,
            domain=self.domain
        )
        if referer is not None:
            self.addSimpleHTTPAuthHeader()

    def geocode(
            self,
            query,
            query_type='StreetAddress',
            maximum_responses=25,
            is_freeform=False,
            filtering=None,
            exactly_one=True,
            timeout=None
    ):  # pylint: disable=W0221,R0913
        """
        Geocode a location query.

        :param string query: The query string to be geocoded; this must
            be URL encoded.

        :param string query_type: The type to provide for geocoding. It can be
            PositionOfInterest, StreetAddress or CadastralParcel.
            StreetAddress is the default choice if none provided.

        :param int maximum_responses: The maximum number of responses
            to ask to the API in the query body.

        :param string is_freeform: Set if return is structured with
            freeform structure or a more structured returned.
            By default, value is False.

        :param string filtering : TODO update
            Provides the geocoder with a hint to the region
            that the query resides in. This value will help the geocoder
            but will not restrict the possible results to the supplied
            region. The bounds parameter should be specified as 4
            coordinate points forming the south-west and north-east
            corners of a bounding box. For example,
            `bounds=-0.563160,51.280430,0.278970,51.683979`.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

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

        xml_request = """<?xml version="1.0" encoding="UTF-8"?>
            <XLS version="1.2"
                 xmlns="http://www.opengis.net/xls"
                 xmlns:gml="http://www.opengis.net/gml"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://www.opengis.net/xls 
                 http://schemas.opengis.net/ols/1.2/olsAll.xsd">
            <RequestHeader srsName="" sessionID=""/>
            <Request methodName="LocationUtilityService" version="1.2"
                     requestID="" maximumResponses="{maximum_responses}">
                <GeocodeRequest returnFreeForm="{is_freeform}">
                    <Address countryCode="{query_type}">
                        <freeFormAddress>{query}</freeFormAddress>
                        {filtering}
                    </Address>
                </GeocodeRequest>
            </Request></XLS>"""

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
            maximum_responses=maximum_responses,
            is_freeform=is_freeform,
            query=query,
            query_type=query_type,
            filtering=filtering
        )

        logger.debug("Request geocode: \n %s", request_string)

        params = {
            'xls': request_string
        }

        url = "?".join((self.api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)

        raw_xml = self.request_raw_content(url, timeout)

        return self._parse_xml(
            raw_xml,
            is_freeform=is_freeform,
            exactly_one=exactly_one
        )

    def reverse(
            self,
            query,
            reverse_geocode_preference=None,
            maximum_responses=25,
            is_freeform=False,
            filtering=None,
            exactly_one=False,
            timeout=None
    ):  # pylint: disable=W0221,R0913
        """
        Given a point, find an address.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s"

        :param boolean exactly_one: Return one result or a list of results, if
            available.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        """

        xml_request = """<?xml version="1.0" encoding="UTF-8"?>
            <XLS version="1.2"
                 xmlns="http://www.opengis.net/xls"
                 xmlns:gml="http://www.opengis.net/gml"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://www.opengis.net/xls 
                 http://schemas.opengis.net/ols/1.2/olsAll.xsd">
                <RequestHeader/>
                <Request methodName="ReverseGeocodeRequest"
                  maximumResponses="{maximum_responses}" requestID=""
                  version="1.2">
                <ReverseGeocodeRequest returnFreeForm="{is_freeform}">
                    {reverse_geocode_preference}
                    <Position>
                      <gml:Point>
                        <gml:pos>{query}</gml:pos>
                      </gml:Point>
                      {filtering}
                    </Position>
                  </ReverseGeocodeRequest>
                </Request>
            </XLS>"""

        if reverse_geocode_preference is None:
            reverse_geocode_preference = ['StreetAddress']

        if not ('StreetAddress' in reverse_geocode_preference or
                'PositionOfInterest' in reverse_geocode_preference):
            raise GeocoderQueryError("""You must provide a list with
            StreetAddress, PositionOfInterest or both for the request""")

        point = self._coerce_point_to_string(query)
        point = point.replace(',', ' ')

        # Manage type change for xml case sensitive
        if is_freeform:
            is_freeform = 'true'
        else:
            is_freeform = 'false'

        # Manage filtering value
        if filtering is None:
            filtering = ''

        reverse_geocode_preference = [
            ('<ReverseGeocodePreference>' +
             pref +
             '</ReverseGeocodePreference>')
            for pref in reverse_geocode_preference]
        reverse_geocode_preference = '\n'.join(reverse_geocode_preference)
        request_string = xml_request.format(
            maximum_responses=maximum_responses,
            is_freeform=is_freeform,
            query=point,
            reverse_geocode_preference=reverse_geocode_preference,
            filtering=filtering
        )

        logger.debug("Request geocode: \n %s", request_string)

        params = {
            'xls': request_string
        }

        url = "?".join((self.api, urlencode(params)))

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)

        raw_xml = self.request_raw_content(url, timeout)

        return self._parse_xml(
            raw_xml,
            exactly_one=exactly_one,
            is_reverse=True,
            is_freeform=is_freeform
        )

    def addSimpleHTTPAuthHeader(self):
        """
        Create Urllib request object embedding HTTP simple authentication
        """
        params = {
            'xls':  """<?xml version="1.0" encoding="UTF-8"?>
                    <XLS version="1.2"
                        xmlns="http://www.opengis.net/xls"
                        xmlns:gml="http://www.opengis.net/gml"
                        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                        xsi:schemaLocation="http://www.opengis.net/xls 
                        http://schemas.opengis.net/ols/1.2/olsAll.xsd">
                    <RequestHeader srsName="" sessionID=""/>
                    <Request methodName="LocationUtilityService" version="1.2"
                            requestID="" maximumResponses="1">
                        <GeocodeRequest returnFreeForm="false">
                            <Address countryCode="PositionOfInterest">
                                <freeFormAddress>rennes</freeFormAddress>
                            </Address>
                        </GeocodeRequest>
                    </Request></XLS>"""
        }

        top_level_url = "?".join((self.api, urlencode(params)))
        password_mgr = HTTPPasswordMgrWithDefaultRealm()

        # Add the username and password.
        # If we knew the realm, we could use it instead of None.
        password_mgr.add_password(
            None,
            top_level_url,
            self.username,
            self.password
        )

        handler = HTTPBasicAuthHandler(password_mgr)

        # create "opener" (OpenerDirector instance)
        opener = build_opener(handler)

        # Install the opener.
        # Now all calls to urllib.request.urlopen use our opener.
        install_opener(opener)

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
            ns = u(ns)
            nsl = len(ns)
            for elem in doc.getiterator():
                if elem.tag.startswith(ns):
                    elem.tag = elem.tag[nsl:]

        remove_namespace(tree, 'http://www.opengis.net/gml')
        remove_namespace(tree, 'http://www.opengis.net/xls')
        remove_namespace(tree, 'http://www.opengis.net/xlsext')

        # Return places as json instead of XML
        places = self._xml_to_json_places(tree, is_reverse=is_reverse)

        if exactly_one:
            return self.parse_place(places[0], is_freeform=is_freeform)
        else:
            return [
                self.parse_place(
                    place,
                    is_freeform=is_freeform
                ) for place in places
            ]

    @staticmethod
    def _xml_to_json_places(tree, is_reverse=False):
        """
        Transform the xml ElementTree due to XML webservice return to json
        """

        select_multi = 'GeocodedAddress'
        if is_reverse:
            select_multi = 'ReverseGeocodedLocation'

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
                    ''
                ) if selector is not None else ''

            place['accuracy'] = testContentAttrib(
                adr.find('.//GeocodeMatchCode'), 'accuracy')

            place['match_type'] = testContentAttrib(
                adr.find('.//GeocodeMatchCode'), 'matchType')

            place['building'] = testContentAttrib(
                adr.find('.//Address/StreetAddress/Building'), 'number')

            place['search_centre_distance'] = testContentAttrib(
                adr.find('.//SearchCentreDistance'), 'value')

            for key, value in iteritems(el):
                if value is not None:
                    place[key] = value.text
                    if value.text == None:
                        place[key] = ''
                else:
                    place[key] = ''

            # We check if lat lng is not empty and unpack accordingly
            if place['pos']:
                lat, lng = place['pos'].split(' ')
                place['lat'] = lat.strip()
                place['lng'] = lng.strip()
            else:
                place['lat'] = place['lng'] = ''

            # We removed the unused key
            place.pop("pos", None)
            places.append(place)

        return places

    def request_raw_content(self, url, timeout):
        """
        Send the request to get raw content.
        """

        request = Request(url)

        if self.referer:
            request.add_header('Referer', self.referer)

        raw_xml = self._call_geocoder(
            request,
            timeout=timeout,
            deserializer=None
        )

        logger.debug("Returned geocode: \n %s", raw_xml)

        return raw_xml


    @staticmethod
    def parse_place(place, is_freeform=None):
        """
        Get the location, lat, lng and place from a single json place.
        """
        # When freeform already so full adress
        if is_freeform == 'true':
            location = place.get('freeformaddress')
        else:
            # When classic geocoding
            if place.get('match_type'):
                location = place.get('postal_code') + ' ' + \
                               place.get('commune')
                if place.get('match_type') in ['Street number',
                                               'Street enhanced']:
                    location = place.get('building') + ' ' + \
                               place.get('street') + ', ' + \
                               location
                elif place.get('match_type') == 'Street':
                    location = place.get('street') + ', ' + \
                               location
            else:
                # For parcelle
                if place.get('numero'):
                    location = place.get('street')
                else:
                    # When reverse geocoding
                    location = place.get('postal_code') + ' ' + \
                               place.get('commune')
                    if place.get('street'):
                        location = place.get('street') + ', ' + \
                                   location
                    if place.get('building'):
                        location = place.get('building') + ' ' + \
                                   location

        latitude = place.get('lat')
        longitude = place.get('lng')

        return Location(location, (latitude, longitude), place)

    def _parse_json(self, page, exactly_one=True):
        """
        Returns location, (latitude, longitude) from json feed
        """
        return page
