Changelog
=========

1.12.0
------
2018-03-TBD

* ADDED: Mapzen geocoder. Contributed by migurski. (#183)

* CHANGED: GoogleV3 geocoder now supports a `channel` option.
    Contributed by gotche. (#206)

* CHANGED: Use the IUGG mean earth radius for EARTH_RADIUS.
    Contributed by cffk. (#151)

* CHANGED: Use the exact conversion factor from kilometers to miles.
    Contributed by cffk. (#150)

* CHANGED: Photon geocoder now accepts a new `limit` option.
    Contributed by Mariana Georgieva.

* CHANGED: Photon geocoder: removed `osm_tag` option from
    reverse geocoding method, as Photon backend doesn't support
    it for reverse geocoding.

* FIXED: Photon geocoder was always returning an empty address.

* FIXED: Yandex geocoder was returning a truncated address
    (the `name` part of a place was missing).

* FIXED: The custom `User-Agent` header was not actually sent.
    This also fixes broken Nominatim, which has recently banned
    the stock urllib user agent.

* FIXED: `geopy.util.get_version()` function was throwing
    an `ImportError` exception instead of returning a version string.

* REMOVED: Navidata geocoder has been removed.
    Contributed by medecau. (#204)


1.11.0
------
2015-09-01

* ADDED: Photon geocoder. Contributed by mthh.

* ADDED: Bing supports structured query parameters. Contributed by
    SemiNormal.

* CHANGED: Geocoders send a `User-Agent` header, which by default is
    `geopy/1.11.0`. Configure it during geocoder initialization. Contributed
    by sebastianneubauer.

* FIXED: Index out of range error with no results using Yandex. Contributed
    by facciocose.

* FIXED: Nominatim was incorrectly sending `view_box` when not requested,
    and formatting it incorrectly. Contributed by m0zes.


1.10.0
------
2015-04-05

* CHANGED: GeocodeFarm now uses version 3 of the service's API, which
    allows use by unauthenticated users, multiple results, and
    SSL/TLS. You may need to obtain a new API key from GeocodeFarm, or
    use `None` for their free tier. Contributed by Eric Palakovich Carr.

* ADDED: DataBC geocoder for use with the British Columbia government's
    DataBC service. Contributed by Benjamin Trigona-Harany.

* ADDED: Placefinder's geocode method now requests a timezone if the
    `with_timezone` parameter is true. Contributed by willr.

* FIXED: Nominatim specifies a `viewbox` parameter rather than the
    apparently deprecated `view_box`.


1.9.1
-----
2015-02-17

* FIXED: Fix support for GoogleV3 bounds parameter. Contributed by
    Benjamin Trigona-Harany.


1.9.0
-----
2015-02-12

* CHANGED: MapQuest geocoder removed as the API it uses is now only available
    to enterprise accounts. OpenMapQuest is a replacement for
    Nominatim-sourced data.

* CHANGED: Nominatim now uses HTTPS by default and accepts a `scheme`
    argument. Contributed by srounet.

* ADDED: Nominatim now accepts a `domain` argument, which
    allows using a different server than `nominatim.openstreetmap.org`.
    Contributed by srounet.

* FIXED: Bing was not accessible from `get_geocoder_for_service`. Contributed
    by Adrián López.


1.8.1
-----
2015-01-28

* FIXED: GoogleV3 geocoder did not send API keys for reverse and timezone
    methods.


1.8.0
-----
2015-01-21

* ADDED: NaviData geocoder added. Contributed by NaviData.

* CHANGED: LiveAddress now requires HTTPS connections. If you set `scheme`
    to be `http`, rather than the default `https`, you will now receive a
    `ConfigurationError`.


1.7.1
-----
2015-01-05

* FIXED: IGN France geocoder's address formatting better handles results
    that do not have a building number. Contributed by Thomas Gratier.


1.7.0
-----
2014-12-30

* ADDED: IGN France geocoder. Contributed by Thomas Gratier.

* FIXED: Bing checks the response body for error codes.


1.6.1
-----
2014-12-12

* FIXED: What3Words validation loosened. Contributed by spatialbitz.

* FIXED: Point.format() includes altitude.


1.6.0
-----
2014-12-08

* ADDED: Python 3.2 and PyPy3 compatibility. Contributed by Mike Toews.


1.5.0
-----
2014-12-07

* ADDED: Yandex geocoder added. Contributed by htch.

* ADDED: What3Words geocoder added. Contributed by spatialbitz.

* FIXED: LiveAddress geocoder made compatible with a change in the service's
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

