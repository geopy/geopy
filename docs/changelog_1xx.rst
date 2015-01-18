1.8.0
-----
master

* ADDED: NaviData geocoder added. Contributed by NaviData.

* CHANGED: LiveAddress now requires HTTPS connections. If you set `scheme`
    to be `http`, rather than the default `https`, you will now receive a
    `ConfigurationError`.


1.7.1
-----
2014-01-05

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

