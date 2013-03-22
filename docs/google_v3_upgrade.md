# Upgrading to GeoPy 0.95 & Google Maps API V3

As of March 2013, it appears that the [Google Maps Geocoding API V2][v2] no longer works in nearly all cases (despite [a Google notice][dep_note] that the sunset period for the V2 API would be extended through to September).

[v2]: https://developers.google.com/maps/documentation/geocoding/v2/
[dep_note]: http://googlegeodevelopers.blogspot.com/2013/03/an-update-on-geocoding-api-v2.html

When using GeoPy 0.94.2 or earlier, you will now encounter this error, whether or not you pass a valid server-side `api_key` into `Google()` (it is possible that older keys instituted before the account-linked keys may still work):

```python
>>> from geopy import geocoders
>>> g = geocoders.Google()
>>> g.geocode("55 Broadway, New York, NY")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/tmp/test/lib/python2.7/site-packages/geopy/geocoders/google.py", line 81, in geocode
    return self.geocode_url(url, exactly_one)
  File "/tmp/test/lib/python2.7/site-packages/geopy/geocoders/google.py", line 88, in geocode_url
    return dispatch(page, exactly_one)
  File "/tmp/test/lib/python2.7/site-packages/geopy/geocoders/google.py", line 107, in parse_xml
    self.check_status_code(status_code)
  File "/tmp/test/lib/python2.7/site-packages/geopy/geocoders/google.py", line 168, in check_status_code
    raise GBadKeyError("The api_key is either invalid or does not match the domain for which it was given.")
geopy.geocoders.google.GBadKeyError: The api_key is either invalid or does not match the domain for which it was given.
```

The following steps should allow you to continue using GeoPy under Google's newest API version:

## Step 1: Upgrade to GeoPy 0.95

Update your copy of geopy:

If you are using pip (which you should):

    pip install -U geopy==0.95
    
If you are using a manually-installed geopy, you may download the package from PyPI:

* https://pypi.python.org/pypi/geopy/0.95

Unzip and run `python setup.py install` as usual.

## Step 2: Move to the Google V3 API

A nearly equivalent version of the GeoPy is available at `geocoders.googlev3.GoogleV3()`.

An example of an updated version of the code block above:

```python
>>> from geopy import geocoders
>>> g = geocoders.GoogleV3()
>>> g.geocode("55 Broadway, New York, NY")
(u'55 Broadway, New York, NY 10006, USA', (40.706777, -74.01285399999999))
```

## API

The API for the `GoogleV3()` object and it's `.geocode()` method are nearly the same.

### GoogleV3()

The following are the standard arguments:

* `protocol` (optional): should be "http" or "https" (default is "http", will change to "https" in a future version)
* `client_id` (optional): Used **only** if you are a paying [Google Maps API for Business][v3_limits] customer. (default: `None`)
* `secret_key` (optional): Used **only** if you are a paying [Google Maps API for Business][v3_limits] customer. (default: `None`)

Note that `GoogleV3()` does not accept `api_key` as the previous version does. See the [usage limits][v3_limits] doc. If you are a Google Maps API for Business customer, use `client_id` and `secret_key`.

[v3_limits]: https://developers.google.com/maps/documentation/geocoding/#Limits

`GoogleV3()` accepts `domain` like the previous version, but this is not useful will be removed in an upcoming version. (Older versions allowed region biasing by using an alternate domain such as `maps.google.co.uk`. The new API only utilizes one domain, "maps.googleapis.com", and allows [region biasing within the API call][region_bias] -- see below on how to add this to your `.geocode()` calls.)

### geocode()

The following are the new arguments to `geocode()`, generally matching [the Google V3 API specification][geocode_spec]:

* `string`: the address you wish to geocode.
* `sensor`: indicates whether request comes from a device with a location sensor. (Required by API, geopy defaults to False.)
* `bounds` (optional): a bounding box of `lat,lng|lat,lng` (southwest_point, northwest_point) points for [viewport biasing][viewport_bias] (see link for more info).
* `region` (optional): a ccTLD two-character code for [region biasing][region_bias] (see link for more info). This replaces the `Google(domain="maps.google.co.uk")` option when setting up the geocoder class.
* `language` (optional): The language in which to return results. ([See documentation][languages].) If not given, Google will attempt to return results in the native language of the country that your machine is located in.

[geocode_spec]: https://developers.google.com/maps/documentation/geocoding/#GeocodingRequests
[viewport_bias]: https://developers.google.com/maps/documentation/geocoding/#Viewports
[region_bias]: https://developers.google.com/maps/documentation/geocoding/#RegionCodes
[languages]: https://developers.google.com/maps/faq#languagesupport


## Status

Within the next few weeks a new update will be released, at which point imports for `Google()` will wrap a `GoogleV3()` object instead.
