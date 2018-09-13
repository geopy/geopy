:orphan:

Changelog
=========
1.17.0
------
2018-09-13

*   ADDED: OpenMapQuest how inherits from Nominatim. This adds support
    for all parameters and queries implemented in Nominatim (such as
    reverse geocoding). (#319)

*   ADDED: Nominatim-based geocoders now support an `extratags` option.
    Contributed by Oleg. (#320)

*   ADDED: Mapbox geocoder. Contributed by William Hammond. (#323)

*   ADDED: ArcGIS now supports custom `domain` and `auth_domain` values.
    Contributed by Albina. (#325)

*   ADDED: Bodies of unsuccessful HTTP responses are now logged
    with `INFO` level.

*   CHANGED: Reverse geocoding methods now issue a warning for string
    queries which cannot be used to construct a Point instance.
    In geopy 2.0 this will become an exception.

*   CHANGED: GoogleV3 now issues a warning when used without an API key.

*   CHANGED: Parameters accepting bounding boxes have been unified to
    accept a pair of diagonal points across all geopy. Previous
    formats are still supported (until geopy 2.0) but now issue
    a warning when used.

*   CHANGED: Path part of the API urls has been moved to class attributes
    in all geocoders, which allows to override them in subclasses.
    Bing and What3Words now store api urls internally differently.

*   FIXED: TomTom and AzureMaps have been passing boolean values for
    `typeahead` in a wrong format (i.e. `0` and `1` instead of
    `false` and `true`).


1.16.0
------
2018-07-28

*   ADDED: ``geopy.extra.rate_limiter.RateLimiter`` class, useful for
    bulk-geocoding a pandas DataFrame. See also the new
    `Usage with Pandas` doc section. (#317)

*   CHANGED: Nominatim now issues a warning when the default user_agent
    is used against `nominatim.openstreetmap.org`. Please always specify
    a custom user-agent when using Nominatim. (#316)


1.15.0
------
2018-07-15

*   ADDED: GeocodeEarth geocoder based on Pelias (ex-Mapzen). (#309)

*   ADDED: TomTom and AzureMaps (based on TomTom) geocoders. (#312)

*   ADDED: HERE geocoder. Contributed by deeplook. (#304)

*   ADDED: Baidu now supports authentication using SK via a new
    `security_key` option.
    Contributed by tony. (#298)

*   ADDED: Nominatim's and Pickpoint's `view_box` option now accepts
    a list of Points or numbers instead of just stringified coordinates.
    Contributed by svalee. (#299)

*   ADDED: Nominatim and Pickpoint geocoders now support a `bounded`
    option, which restricts results to the items strictly contained
    within the `view_box`.
    Contributed by Karimov Dmitriy. (#182)

*   ADDED: `proxies` param of geocoders can now accept a single string
    instead of a dict. See the updated docs for
    the ``geopy.geocoders.options.default_proxies`` attribute for
    more details.
    Contributed by svalee. (#300)

*   CHANGED: Mapzen has been renamed to Pelias, `domain` parameter has
    been made required. (#309)

*   CHANGED: What3Words API has been updated from v1 to v2.
    Please note that `Location.raw` results have changed due to that.
    Contributed by Jonathan Batchelor. (#226)

*   FIXED: Baidu mistakenly didn't process the returned errors correctly.
    Contributed by tony. (#298)

*   FIXED: `proxies={}` didn't reset system proxies as expected.


1.14.0
------
2018-05-13

This release contains a lot of public API cleanup. Also make sure to
check out the updated docs! A new `Semver` doc section has been added,
explaining the geopy's policy on breaking changes.

*   ADDED: Nominatim geocoder now supports an `addressdetails` option in
    the `reverse` method.
    Contributed by Serphentas. (#285)

*   ADDED: ArcGIS geocoder now supports an `out_fields` option in
    the `geocode` method.
    Contributed by Jonathan Batchelor. (#227)

*   ADDED: Yandex geocoder now supports a `kind` option in the
    `reverse` method.

*   ADDED: Some geocoders were missing `format_string` option. Now all
    geocoders support it.

*   ADDED: `geopy.distance.lonlat` function for conveniently converting
    `(x, y, [z])` coordinate tuples to the `Point` instances, which use
    `(y, x, [z])`.
    Contributed by svalee. (#282)

*   ADDED: `geopy.geocoders.options` object, which allows to configure
    geocoder defaults (such as User-Agent, timeout, format_string)
    application-wide. (#288)

*   ADDED: Support for supplying a custom SSL context. See docs for
    `geopy.geocoders.options.default_ssl_context`. (#291)

*   ADDED: Baidu geocoder was missing the `exactly_one` option in its `reverse`
    method.

*   ADDED: GeocodeFarm now supports a `scheme` option.

*   CHANGED: Baidu and Yandex geocoders now use https scheme by default
    instead of http.

*   CHANGED: ArcGIS geocoder was updated to use the latest API.
    Please note that `Location.raw` results for `geocode` have changed
    a little due to that.
    Contributed by Jonathan Batchelor. (#227)

*   CHANGED: Explicitly passed `timeout=None` in geocoder calls now
    issues a warning. Currently it means "use geocoder's default timeout",
    while in geopy 2.0 it would mean "use no timeout". (#288)

*   CHANGED: GoogleV3 `geocode` call now supports `components` without
    `query` being specified. (#296)

*   CHANGED: GeoNames, GoogleV3, IGNFrance, OpenCage and Yandex erroneously
    had `exactly_one=False` by default for `reverse` methods, which must have
    been True. This behavior has been kept, however a warning will be issued
    now unless `exactly_one` option is explicitly specified in `reverse` calls
    for these geocoders. The default value will be changed in geopy 2.0. (#295)

*   CHANGED: Point now throws a `ValueError` exception instead of normalizing
    latitude and tolerating NaN/inf values for coordinates. (#294)

*   CHANGED: `Vincenty` usage now issues a warning. `Geodesic` should be used
    instead. Vincenty is planned to be removed in geopy 2.0. (#293)

*   CHANGED: ArcGIS `wkid` option for `reverse` call has been deprecated
    because it was never working properly, and it won't, due to
    the coordinates normalization in Point.

*   FIXED: ArcGIS and What3Words did not respect `exactly_one=False`.
    Now they respect it and return a list of a single location in this case.

*   FIXED: ArcGIS was throwing an exception on empty response of `reverse`.
    Now `None` is returned, as expected.

*   FIXED: `GeocodeFarm` was raising an exception on empty response instead
    of returning `None`. Contributed by Arthur Pemberton. (#240)

*   FIXED: `GeocodeFarm` had missing `Location.address` value sometimes.

*   REMOVED: `geopy.geocoders.DEFAULT_*` constants (in favor of
    `geopy.geocoders.options.default_*` attributes). (#288)

*   REMOVED: YahooPlaceFinder geocoder. (#283)

*   REMOVED: GeocoderDotUS geocoder. (#286)


1.13.0
------
2018-04-12

*   ADDED: Pickpoint geocoder. Contributed by Vladimir Kalinkin. (#246)

*   ADDED: Bing geocoder: additional parameters for geocoding (`culture`
    and `include_country_code`). Contributed by Bernd Schlapsi. (#166)

*   ADDED: `Point` and `Location` instances are now picklable.

*   ADDED: More accurate algorithm for distance computation
    `geopy.distance.geodesic`, which is now a default
    `geopy.distance.distance`. Vincenty usage is now discouraged in favor of
    the geodesic. This also has added a dependency of geopy on
    `geographiclib` package. Contributed by Charles Karney. (#144)

*   ADDED: Nominatim geocoder now supports a `limit` option and uses `limit=1`
    for `exactly_one=True` requests. Contributed by Serphentas. (#281)

*   CHANGED: `Point` now issues warnings for incorrect or ambiguous inputs.
    Some of them (namely not finite values and out of band latitudes)
    will be replaced with ValueError exceptions in the future versions
    of geopy. (#272)

*   CHANGED: `Point` now uses `fmod` instead of `%` which results in more
    accurate coordinates normalization. Contributed by svalee. (#275, #279)

*   CHANGED: When using http proxy, urllib's `install_opener` was used, which
    was altering `urlopen` call globally. It's not used anymore.

*   CHANGED: `Point` now raises `ValueError` instead of `TypeError` when more
    than 3 arguments have been passed.

*   FIXED: `Point` was raising an exception when compared to non-iterables.

*   FIXED: Coordinates of a `Point` instance changed via `__setitem__` were
    not updating the corresponding lat/long/alt attributes.

*   FIXED: Coordinates of a `Point` instance changed via `__setitem__` were
    not being normalized after assignment. Note, however, that attribute
    assignments are still not normalized. (#272)

*   FIXED: `Distance` instances comparison was not working in Python3.

*   FIXED: Yandex geocoder was sending API key with an incorrect parameter.

*   FIXED: Unit conversions from feet were incorrect.
    Contributed by scottessner. (#162)

*   FIXED: Vincenty destination function had an error in the formula
    implementation. Contributed by Hanno Schlichting. (#194)

*   FIXED: Vincenty was throwing UnboundLocalError when difference between
    the two longitudes was close to 2*pi or either of them was NaN. (#187)

*   REMOVED: `geopy.util.NullHandler` logging handler has been removed.


1.12.0
------
2018-03-13

*   ADDED: Mapzen geocoder. Contributed by migurski. (#183)

*   ADDED: GoogleV3 geocoder now supports a `channel` option.
    Contributed by gotche. (#206)

*   ADDED: Photon geocoder now accepts a new `limit` option.
    Contributed by Mariana Georgieva.

*   CHANGED: Use the IUGG mean earth radius for EARTH_RADIUS.
    Contributed by cffk. (#151)

*   CHANGED: Use the exact conversion factor from kilometers to miles.
    Contributed by cffk. (#150)

*   CHANGED: OpenMapQuest geocoder now properly supports `api_key`
    option and makes it required.

*   CHANGED: Photon geocoder: removed `osm_tag` option from
    reverse geocoding method, as Photon backend doesn't support
    it for reverse geocoding.

*   FIXED: Photon geocoder was always returning an empty address.

*   FIXED: Yandex geocoder was returning a truncated address
    (the `name` part of a place was missing).

*   FIXED: The custom `User-Agent` header was not actually sent.
    This also fixes broken Nominatim, which has recently banned
    the stock urllib user agent.

*   FIXED: `geopy.util.get_version()` function was throwing
    an `ImportError` exception instead of returning a version string.

*   FIXED: Docs for constructing a `geopy.point.Point` were referencing
    latitude and longitude in a wrong order. Contributed by micahcochran
    and sjorek. (#207 #229)

*   REMOVED: Navidata geocoder has been removed.
    Contributed by medecau. (#204)


1.11.0
------
2015-09-01

*   ADDED: Photon geocoder. Contributed by mthh.

*   ADDED: Bing supports structured query parameters. Contributed by
    SemiNormal.

*   CHANGED: Geocoders send a `User-Agent` header, which by default is
    `geopy/1.11.0`. Configure it during geocoder initialization. Contributed
    by sebastianneubauer.

*   FIXED: Index out of range error with no results using Yandex. Contributed
    by facciocose.

*   FIXED: Nominatim was incorrectly sending `view_box` when not requested,
    and formatting it incorrectly. Contributed by m0zes.


1.10.0
------
2015-04-05

*   CHANGED: GeocodeFarm now uses version 3 of the service's API, which
    allows use by unauthenticated users, multiple results, and
    SSL/TLS. You may need to obtain a new API key from GeocodeFarm, or
    use `None` for their free tier. Contributed by Eric Palakovich Carr.

*   ADDED: DataBC geocoder for use with the British Columbia government's
    DataBC service. Contributed by Benjamin Trigona-Harany.

*   ADDED: Placefinder's geocode method now requests a timezone if the
    `with_timezone` parameter is true. Contributed by willr.

*   FIXED: Nominatim specifies a `viewbox` parameter rather than the
    apparently deprecated `view_box`.


1.9.1
-----
2015-02-17

*   FIXED: Fix support for GoogleV3 bounds parameter. Contributed by
    Benjamin Trigona-Harany.


1.9.0
-----
2015-02-12

*   CHANGED: MapQuest geocoder removed as the API it uses is now only available
    to enterprise accounts. OpenMapQuest is a replacement for
    Nominatim-sourced data.

*   CHANGED: Nominatim now uses HTTPS by default and accepts a `scheme`
    argument. Contributed by srounet.

*   ADDED: Nominatim now accepts a `domain` argument, which
    allows using a different server than `nominatim.openstreetmap.org`.
    Contributed by srounet.

*   FIXED: Bing was not accessible from `get_geocoder_for_service`. Contributed
    by Adrián López.


1.8.1
-----
2015-01-28

*   FIXED: GoogleV3 geocoder did not send API keys for reverse and timezone
    methods.


1.8.0
-----
2015-01-21

*   ADDED: NaviData geocoder added. Contributed by NaviData.

*   CHANGED: LiveAddress now requires HTTPS connections. If you set `scheme`
    to be `http`, rather than the default `https`, you will now receive a
    `ConfigurationError`.


1.7.1
-----
2015-01-05

*   FIXED: IGN France geocoder's address formatting better handles results
    that do not have a building number. Contributed by Thomas Gratier.


1.7.0
-----
2014-12-30

*   ADDED: IGN France geocoder. Contributed by Thomas Gratier.

*   FIXED: Bing checks the response body for error codes.


1.6.1
-----
2014-12-12

*   FIXED: What3Words validation loosened. Contributed by spatialbitz.

*   FIXED: Point.format() includes altitude.


1.6.0
-----
2014-12-08

*   ADDED: Python 3.2 and PyPy3 compatibility. Contributed by Mike Toews.


1.5.0
-----
2014-12-07

*   ADDED: Yandex geocoder added. Contributed by htch.

*   ADDED: What3Words geocoder added. Contributed by spatialbitz.

*   FIXED: LiveAddress geocoder made compatible with a change in the service's
    authentication. An `auth_id` parameter was added to the geocoder's
    initialization. Contributed by Arsen Mamikonyan.


1.4.0
-----
2014-11-08

*   ADDED: Mapquest.reverse() method added. Contributed by Dody Suria Wijaya.

*   ADDED: Bing's geocoder now accepts the optional arguments "culture",
    "includeNeighborhood", and "include". Contributed by oskholl.


1.3.0
-----
2014-09-23

*   ADDED: Nominatim.geocode() accepts a `geometry` argument for
    retrieving `wkt`, `svg`, `kml`, or `geojson` formatted geometries
    in results. Contributed by spatialbitz.


1.2.0
-----
2014-09-22

*   ADDED: GeoNames.reverse() added. Contributed by Emile Aben.

*   ADDED: GoogleV3.timezone() added. This returns a pytz object
    giving the timezone in effect for a given location at a time
    (defaulting to now).


1.1.5
-----
2014-09-07

*   FIXED: YahooPlaceFinder is now compatible with the older
    requests_oauthlib version 0.4.0.


1.1.4
-----
2014-09-06

*   FIXED: Point.format() seconds precision in Python 3.


1.1.3
-----
2014-08-30

*   FIXED: Fix OpenCage AttributeError on empty result. Contributed
    by IsaacHaze.


1.1.2
-----
2014-08-12

*   FIXED: Update Point __repr__ method to format _items properly.
    Contributed by TristanH.


1.1.1
-----
2014-08-06

*   FIXED: Python 3 compatibility.


1.1.0
-----
2014-07-31

*   ADDED: OpenCage geocoder added. Contributed by Demeter Sztanko.

*   ADDED: `geopy.geocoders.get_geocoder_for_service` allows library authors
    to dynamically get a geocoder.

*   FIXED: YahooPlacefinder bugs causing geocoding failure.

*   FIXED: LiveAddress API URL updated.

*   FIXED: Location.__repr__ unicode encode error in Python 2.7.

*   CHANGED: `geopy.geocoders` modules now strictly declare their exports.


1.0.1
-----
2014-07-24

*   FIXED: The Baidu Maps geocoder's `_check_status` method used a Python
    2-specific print statement.


1.0.0
-----
2014-07-23

*   ADDED: Baidu Maps geocoder added. Contributed by Risent.

*   ADDED: Nominatim geocoder now supports structured queries. Contributed
    by kpanic.

*   ADDED: Nominatim geocoder now supports a `language` parameter. Contributed
    by Benjamin Henne.

*   CHANGED: GoogleV3's `geocode` and `reverse` methods have different
    orders for keyword argument parameters. Geocoders are now
    standardized on `(query, exactly_one, timeout, ...)`.

*   FIXED: Removed rounding of minutes which was causing a formatted point
    to always have zero seconds. Contributed by Jonathan Batchelor.

