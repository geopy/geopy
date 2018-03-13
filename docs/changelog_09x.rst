:orphan:

Changelog of the 0.9 series
===========================

0.99
----
2014-03-18

*   ADDED: GeocodeFarm geocoder added with support for geocoding and reverse
    geocoding. Contributed by Eric Palakovich Carr.


0.98.3
------
2014-03-07

*   ADDED: Queries are encoded as unicode in Python 2.7 by the geocoder.
    Contributed by Rocky Meza.

*   FIXED: YahooPlaceFinder `count` parameter fixed.

*   FIXED: Point.__repr__ fixed. Contributed by Paweł Mandera.


0.98.2
------
2014-02-28

*   ADDED: GoogleV3 now accepts an `api_key` parameter. Contributed
    by Andrea Tosatto.

*   CHANGED: GoogleV3's deprecated `protocol` argument has been removed.


0.98.1
------
2014-02-22

*   FIXED: Mapquest geocoder did not use format_string in the creation
    of its queries. Contributed by Danny Finkelstein.

*   FIXED: Geocoders incorrectly raised a GeocoderTimedOut exception for all
    `SSLError` exceptions. Contributed by David Gilman.


0.98
----
2014-02-05

*   CHANGED: Geocoders' `geocode` and `reverse` method return types
    have changed from None, a tuple, or a list of tuples, to None,
    a `geopy.Location` object, or a list of `geopy.Location` objects.

    `Location` objects can be iterated over the same as
    the previous tuples for backwards compatibility, returning
    (address<String>, (latitude<float>, longitude<Float)).

    `geopy.Location` objects also make returned data available as
    properties. Existing attributes are `address`, `longitude`, and
    `latitude`. Now available are the geocoder's raw response as `raw`,
    and the location's altitude as `altitude`.


0.97.1
------
2014-02-01

*   FIXED:YahooPlaceFinder geocoder authentication and response parsing fixed.
    Contributed by petergx.

*   ADDED: GoogleV3 geocoding now supports a `components` parameter, which
    is a filter for location criteria such as administrative area,
    country, etc. Contributed by crccheck.


0.97
----
2013-12-26

*   CHANGED: SSL connections are used by default for services with support.
    These geocoders accept a new 'scheme' argument in their init,
    which may be 'https' or 'http'. Users desiring unencrypted
    connections must now specify 'http'. Note that SSL connections'
    certificates are not verified.

*   CHANGED: Geocoders accept a `timeout` argument which specifies the
    number of seconds to wait before raising a `GeocoderTimedOut` exception.
    This can be specified in the init, or specified one-off in each `geocode`
    or `reverse` call. There is now a default of 1 second.

*   CHANGED: geopy now supports Python 2 and Python 3 on a single codebase.
    Support for Python 2.5 is also dropped.

*   CHANGED: GoogleV3's `protocol` argument is deprecated in favor of `scheme`.

*   ADDED: ESRI's ArcGIS geocoder implemented. Contributed by Arsen Mamikonyan.

*   ADDED: Geocoders accept a `proxies` argument which specifies a proxy to
    route its geocoder requests through. It uses urllib, and accepts
    proxies in the form of a dictionary of {scheme: proxy address}, e.g.,
    {"https": "192.0.2.0"}. This was present but undocumented in 0.96.

*   ADDED: Geocoders check a new method, `_geocoder_exception_handler`, if
    defined, when the HTTP call to the geocoder's service raises an
    exception. See LiveStreets for an example. Users can define or
    override this method.

*   ADDED: LiveStreets throws a `GeocoderQuotaExceeded` exception when
    appropriate.

*   ADDED: `Point` can parse a greater variety of coordinate strings.
    Contributed by nucflash.

*   FIXED: GeocodersDotUS now authenticates with an `Authorization`
    HTTP header. Contributed by Arsen Mamikonyan.

*   REMOVED: MediaWiki and SemanticMediaWiki geocoders removed.

*   REMOVED: Geohash module has been removed.


0.96.3
------
2013-12-26

*   ADDED: Documentation warning that the Vincenty distance implementation fails
    to converge for some valid points. Reported by mkeller-upb.

*   FIXED: Geocoder proxying fixed. Contributed by Marc-Olivier Titeux.


0.96.2
------
2013-11-20

*   FIXED: MANIFEST.in exclusions broke builds under `buildout`.
    Contributed by James Mills.


0.96.1
------
2013-10-31

*   FIXED: GoogleV3 returns `None` when the service returns an error status of
    `ZERO_RESULTS`. Contributed by Ian A Wilson.


0.96
----
2013-10-25

*   CHANGED: GoogleV3's reverse geocoder now returns one result by default. Set
    `exactly_one` to False for a list.

*   CHANGED: GoogleV3 returns new exception types:
    `geopy.geocoders.base.GQueryError` -> `geopy.exc.GeocoderQueryError`
    `geopy.geocoders.base.GeocoderResultError` -> `geopy.exc.GeocoderQueryError`
    `geopy.geocoders.base.GTooManyQueriesError` -> `geopy.exc.GeocoderQuotaExceeded`

*   ADDED: OpenStreetMap Nominatim geocoder implemented. Contributed by
    Alessandro Pasotti.

*   ADDED: Yahoo! BOSS Geo PlaceFinder geocoder implemented. Contributed by
    jhmaddox and Philip Kimmey.

*   ADDED: SmartyStreets LiveAddress geocoder implemented. Contributed by
    Michael Whatcott.

*   ADDED: GeoNames geocoder is implements GeoNames' new username
    requirement and `api.geonames.org` endpoint. Contributed by David
    Wilson and Benoit Grégoire.

*   ADDED: Bing geocoder supports `user_location` (`Point`) parameter. Bing will
    prefer results near the coordinates of `user_location`. Contributed by
    Ryan Nagle.

*   FIXED: `GoogleV3.geocode_first()` no longer throws exception on multiple
    results. Contributed by migajek.

*   FIXED: Unnecessary coercing to UTF-8 on Py3k. Contributed by akanouras.

*   FIXED: `format_degrees` now rounds minutes properly. Contributed by avdd.

*   FIXED: No longer warn if the optional dependency `BeautifulSoup` is
    not present.

*   FIXED: Miscellaneous inconsistent behavior and errors in geolocating.

*   REMOVED: Google V2 geocoder has been removed as its API was shutdown.


0.95.1
------
2013-03-22

*   FIXED: Fix `DeprecationWarning` showing for GoogleV2 even if
    it wasn't being used (due to `geopy.geocoders` importing it).
    Contributed by Dave Arter.

*   CHANGED: `GoogleV3.geocode` "address" kwarg renamed to "string" to match
    `Google.geocode` to make updating easier.

*   FIXED: Geocoders now properly handle Unicode objects as input (previously
    would fail on non-ASCII characters due to wanting UTF-8 strings).


0.95
----
2013-03-12

*   ADDED: Google Geocoding API V3 support. Contributed by Jordan Bouvier
    (jbouvier). "google.Google()" should be replaced by
    "googlev3.GoogleV3()", with no `api_key`.

    Please see http://goo.gl/somDT for valid arguments.

*   CHANGED: setup.py updated to now automatically support Python 3+ (via 2to3
    auto-compile option). Contributed by Feanil Patel.


0.94.2
------
2012-03-12

*   ADDED: MANIFEST.in so that LICENSE file gets included in dist packages
    (per req by Debian Python Module Team)

*   CHANGED: Yahoo geocoder uses new PlaceFinder API instead of outdated
    MapsService V1 API.


0.94.1
------
2011-03-24

*   ADDED:  Test suite includes geocoding tests for the Google, Bing, Yahoo,
    GeocoderDotUS, and GeoNames geocoders.

*   CHANGED: `output_format` is deprecated in backends that used it.

*   FIXED:  Bing geocoder now works properly. Updated to use the JSON return
    method rather than XML. `output_format` has always been ignored
    and is now deprecated.

*   FIXED:  GeocoderDotUS now works properly. Updated to use more compact CSV
    return method rather than XMLRPC.

*   CHANGED: Yahoo geocoder now uses the "old" tuple return format
    (address, (lat, lon)) rather than the undocumented Location()
    object, for API consistency. (Object return values with rich
    data will be implemented in a future release.)

*   FIXED:  Fixed "print" statement in Bing backend. No more
    print statements remain.

*   FIXED:  In addition to checking for system `json` and `simplejson`,
    geopy now looks for a system-installed `django` (which bundles a
    copy of simplejson).

*   FIXED:  Implement __cmp__ on Distance so that distance objects may
    be compared against one another.

*   CHANGED: Added __repr__ and __str__ to Distance

*   ADDED:  Geocoder backend for MapQuest's OpenMapQuest API,
    contributed by Shashwat Anand.


0.94
----
2010-03-07

*   ADDED: Partial test suite can now be run via "setup.py test"

*   FIXED: Converted "print" statements to logger calls to
    allow compatibility with WSGI.

*   FIXED: Google geocoder backend now throws more descriptive
    exceptions on certain failure statuses.

*   FIXED: Add simplejson to install_requires for setup. Use
    native (Python 2.6+/3.0+) json module if available.

*   FIXED: Distance calculations for values beyond
    180/-180 and 90/-90 now wrap instead of raising an error.

*   FIXED: Fixed string representation of Point objects so
    that they don't throw an exception.

*   FIXED: Fixed GreatCircleDistance ValueErrors due to floating
    point precision on extremely close points.


Changes between 0.93 (2006-10-08) and 2009-02-15
------------------------------------------------

See https://github.com/geopy/geopy/compare/0451a051...ffebd5f3
