# geopy
geopy is a Python 2 and 3 client for several popular geocoding web services.

geopy makes it easy for Python developers to locate the coordinates of
addresses, cities, countries, and landmarks across the globe using third-party
geocoders and other data sources.

geopy includes geocoder classes for the [ESRI ArcGIS][arcgis], [OpenStreetMap Nominatim][nominatim], [Google Geocoding API (V3)][google_v3],
[Yahoo! BOSS][yahoo], [geocoder.us][geocoderus], [GeocodeFarm][geocodefarm], and [Bing Maps API][bing]
geocoder services, as well as several other. The various geocoder classes are located in
[geopy.geocoders][geocoders_src].

[arcgis]: http://resources.arcgis.com/en/help/arcgis-rest-api/
[nominatim]: https://wiki.openstreetmap.org/wiki/Nominatim
[google_v3]: https://developers.google.com/maps/documentation/geocoding/
[yahoo]: http://developer.yahoo.com/maps/rest/V1/geocode.html
[bing]: http://www.microsoft.com/maps/developers/web.aspx
[geocoderus]: http://geocoder.us/
[geocodefarm]: https://www.geocodefarm.com/
[opencage]: http://geocoder.opencagedata.com/api.html
[geocoders_src]: https://github.com/geopy/geopy/tree/master/geopy/geocoders

© GeoPy Project and individual contributors under the
[MIT License](https://github.com/geopy/geopy/blob/master/LICENSE).

## Installation

Using [pip](http://www.pip-installer.org/en/latest/):

    pip install geopy

Or, manually: [download the tarball from PyPI](https://pypi.python.org/pypi/geopy),
unzip, and execute this in the same directory:

    python setup.py install

## Geocoding

To geolocate a query to an address and coordinates:

    >>> from geopy.geocoders import GoogleV3
    >>> geolocator = GoogleV3()
    >>> address, (latitude, longitude) = geolocator.geocode("175 5th Avenue NYC")
    >>> print(address, latitude, longitude)
    175 5th Avenue, New York, NY 10010, USA 40.7410262 -73.9897806

To find the address corresponding to a set of coordinates:

    >>> from geopy.geocoders import GoogleV3
    >>> geolocator = GoogleV3()
    >>> address, (latitude, longitude) = geolocator.reverse("40.752067, -73.977578")
    >>> print(address, latitude, longitude)
    77 East 42nd Street, New York, NY 10017, USA 40.7520802 -73.9775683

## Measuring Distance

Geopy can calculate geodesic distance between two points using the
[Vincenty distance](https://en.wikipedia.org/wiki/Vincenty's_formulae) or
[great-circle distance](https://en.wikipedia.org/wiki/Great-circle_distance)
formulas, with a default of Vincenty available as the class
`geopy.distance.distance`, and the computed distance available as attributes
(e.g., `miles`, `meters`, etc.).

Here's an example usage of Vincenty distance:

    >>> from geopy.distance import vincenty
    >>> newport_ri = (41.49008, -71.312796)
    >>> cleveland_oh = (41.499498, -81.695391)
    >>> vincenty(newport_ri, cleveland_oh).miles
    538.3904451566326

Using great-circle distance:

    >>> from geopy.distance import great_circle
    >>> newport_ri = (41.49008, -71.312796)
    >>> cleveland_oh = (41.499498, -81.695391)
    >>> great_circle(newport_ri, cleveland_oh).miles
    537.1485284062816

## Documentation

More documentation and examples can be found at
[Read the Docs](http://geopy.readthedocs.org/en/latest/).
