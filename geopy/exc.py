"""
Exceptions raised by geopy.
"""

class GeocoderError(Exception):
    """
    Catch-all geopy exception.
    """

class GeocoderAuthenticationFailure(GeocoderError):
    """
    The remote geocoding service rejects the API key or account
    credentials this geocoder was instantiated with.
    """

class GeocoderInsufficientPrivileges(GeocoderError):
    """
    The remote geocoding service refused to fulfill a request using the
    account credentials given.
    """

class ConfigurationError(GeocoderError):
    """
    When instantiating a geocoder, the arguments given were invalid. See
    the documentation of each geocoder's `__init__` for more details.
    """

class GeocoderQueryError(GeocoderError):
    """
    The remote geocoding service raised a bad request over the user's input.
    """

class GeocoderQuotaExceeded(GeocoderError):
    """
    The remote geocoding service reports refused to fulfill the request
    because the client has used its quota.
    """

class GeocoderServiceError(GeocoderError):
    """
    Catch-all for exceptions caused when making a call to the geocoding
    service.
    """

class GeocoderTimedOut(GeocoderError):
    """
    The call to the geocoding service was aborted because no response
    was receiving within the geocoding class' `timeout` argument. The
    timeout can be changed when instantiating the geocoder, or on each
    request.
    """
