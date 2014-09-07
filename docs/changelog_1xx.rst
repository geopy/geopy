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

