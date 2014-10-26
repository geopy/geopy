"""
Exceptions raised by geopy.
"""

class GeopyError(Exception):
    """
    Geopy-specific exceptions are all inherited from GeopyError.
    """

class ConfigurationError(GeopyError):
    """
    When instantiating a geocoder, the arguments given were invalid. See
    the documentation of each geocoder's `__init__` for more details.
    """

class GeocoderServiceError(GeopyError):
    """
    There was an exception caused when calling the remote geocoding service,
    and no more specific exception could be raised by geopy. When calling
    geocoders' `geocode` or `reverse` methods, this is the most general
    exception that can be raised, and any non-geopy exception will be caught
    and turned into this. The exception's message will be that of the
    original exception.
    """

class GeocoderQueryError(GeocoderServiceError):
    """
    Either geopy detected input that would cause a request to fail,
    or a request was made and the remote geocoding service responded
    that the request was bad.
    """

class GeocoderQuotaExceeded(GeocoderServiceError):
    """
    The remote geocoding service refused to fulfill the request
    because the client has used its quota.
    """

class GeocoderAuthenticationFailure(GeocoderServiceError):
    """
    The remote geocoding service rejects the API key or account
    credentials this geocoder was instantiated with.
    """

class GeocoderInsufficientPrivileges(GeocoderServiceError):
    """
    The remote geocoding service refused to fulfill a request using the
    account credentials given.
    """

class GeocoderTimedOut(GeocoderServiceError):
    """
    The call to the geocoding service was aborted because no response
    was receiving within the `timeout` argument of either the geocoding class
    or, if specified, the method call. Some services are just consistently
    slow, and a higher timeout may be needed to use them.
    """

class GeocoderUnavailable(GeocoderServiceError):
    """
    Either it was not possible to establish a connection to the remote
    geocoding service, or the service responded with a code indicating
    it was unavailable.
    """

class GeocoderParseError(GeocoderServiceError):
    """
    Geopy could not parse the service's response. This is a bug in geopy.
    """

class GeocoderNotFound(GeopyError):
    """
    Caller requested the geocoder matching a string, e.g.,
    "google" > GoogleV3, but no geocoder could be found.
    """
