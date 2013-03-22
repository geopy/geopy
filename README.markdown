## geopy

© GeoPy Project and individual contributors,
[MIT License](https://github.com/geopy/geopy/blob/master/LICENSE)

geopy is a Python client for several popular geocoding web services.

geopy makes it easy for Python developers to locate the coordinates of
addresses, cities, countries, and landmarks across the globe using third-party
geocoders and other data sources.

### Notes

* Having `geopy.geocoders.google.GBadKeyError` issues with Google geocoder?
  [You can fix that by updating GeoPy and updating your code.](https://github.com/geopy/geopy/tree/master/docs/google_v3_upgrade.md)

### Getting Started

geopy includes geocoder classes for the [Google Geocoding API (V3)][google_v3],
the [Yahoo! geocoder][yahoo], [geocoder.us][geocoderus], [Bing Maps API][bing],
and several more Geocoder API services. The various geocoder classes are located in
[geopy.geocoders][geocoders_src].

[google_v3]: https://developers.google.com/maps/documentation/geocoding/
[yahoo]: http://developer.yahoo.com/maps/rest/V1/geocode.html
[bing]: http://www.microsoft.com/maps/developers/web.aspx
[geocoderus]: http://geocoder.us/
[geocoders_src]: https://github.com/geopy/geopy/tree/master/geopy/geocoders

#### Basic Geocoding

**Examples**

Using the GoogleV3 geocoder:

    >>> from geopy import geocoders
    >>> g = geocoders.GoogleV3()
    >>> place, (lat, lng) = g.geocode("10900 Euclid Ave in Cleveland")
    >>> print "%s: %.5f, %.5f" % (place, lat, lng)
    10900 Euclid Ave, Cleveland, OH 44106, USA: 41.50489, -81.61027

Using the Yahoo! geocoder ([requires an Application ID](http://developer.yahoo.com/faq/index.html#appid)):

    >>> from geopy import geocoders
    >>> y = geocoders.Yahoo('YOUR_APP_ID_HERE')
    >>> place, (lat, lng) = y.geocode("Thames Street, Newport, RI")
    >>> print "%s: %.5f, %.5f" % (place, lat, lng)
    [241-251] THAMES ST, NEWPORT, RI 02840, US: 41.48696, -71.31490

More documentation and examples can be found on the [old Google Code documentation site](http://code.google.com/p/geopy/w/list).
