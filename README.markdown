# geopy

© GeoPy Project and individual contributors,
[MIT License](https://github.com/geopy/geopy/blob/master/LICENSE)

geopy is a Python client for several popular geocoding web services.

geopy makes it easy for Python developers to locate the coordinates of
addresses, cities, countries, and landmarks across the globe using third-party
geocoders and other data sources.

geopy includes geocoder classes for the [Google Geocoding API (V3)][google_v3],
the [Yahoo! BOSS geocoder][yahoo], [geocoder.us][geocoderus], [Bing Maps API][bing],
and several more Geocoder API services. The various geocoder classes are located in
[geopy.geocoders][geocoders_src].

[google_v3]: https://developers.google.com/maps/documentation/geocoding/
[yahoo]: http://developer.yahoo.com/maps/rest/V1/geocode.html
[bing]: http://www.microsoft.com/maps/developers/web.aspx
[geocoderus]: http://geocoder.us/
[geocoders_src]: https://github.com/geopy/geopy/tree/master/geopy/geocoders

## Installation

Using [pip](http://www.pip-installer.org/en/latest/):

    pip install geopy

Or, manually: [download the tarball from PyPI](https://pypi.python.org/pypi/geopy),
unzip, and execute this in the same directory:

    python setup.py install

## Usage

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

## Documentation

More documentation and examples can be found at
[Read the Docs](http://geopy.readthedocs.org/en/latest/).
