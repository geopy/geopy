"""
Exceptions raised by geopy.
"""


class GeopyError(Exception):
    """
    Geopy-specific exceptions are all inherited from GeopyError.
    """


class ConfigurationError(GeopyError, ValueError):
    """
    When instantiating a geocoder, the arguments given were invalid. See
    the documentation of each geocoder's ``__init__`` for more details.
    """


class GeocoderServiceError(GeopyError):
    """
    There was an exception caused when calling the remote geocoding service,
    and no more specific exception could be raised by geopy. When calling
    geocoders' ``geocode`` or `reverse` methods, this is the most generic
    exception that can be raised, and any non-geopy exception will be caught
    and turned into this. The exception's message will be that of the
    original exception.
    """


class GeocoderQueryError(GeocoderServiceError, ValueError):
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


class GeocoderRateLimited(GeocoderQuotaExceeded, IOError):
    """
    The remote geocoding service has rate-limited the request.
    Retrying later might help.

    Exception of this type has a ``retry_after`` attribute,
    which contains amount of time (in seconds) the service
    has asked to wait. Might be ``None`` if there were no such
    data in response.

    .. versionadded:: 2.2
    """

    def __init__(self, message, *, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


class GeocoderAuthenticationFailure(GeocoderServiceError):
    """
    The remote geocoding service rejected the API key or account
    credentials this geocoder was instantiated with.
    """


class GeocoderInsufficientPrivileges(GeocoderServiceError):
    """
    The remote geocoding service refused to fulfill a request using the
    account credentials given.
    """


class GeocoderTimedOut(GeocoderServiceError, TimeoutError):
    """
    The call to the geocoding service was aborted because no response
    has been received within the ``timeout`` argument of either
    the geocoding class or, if specified, the method call.
    Some services are just consistently slow, and a higher timeout
    may be needed to use them.
    """


class GeocoderUnavailable(GeocoderServiceError, IOError):
    """
    Either it was not possible to establish a connection to the remote
    geocoding service, or the service responded with a code indicating
    it was unavailable.
    """


class GeocoderParseError(GeocoderServiceError):
    """
    Geopy could not parse the service's response. This is probably due
    to a bug in geopy.
    """


class GeocoderNotFound(GeopyError, ValueError):
    """
    Caller requested the geocoder matching a string, e.g.,
    ``"google"`` > ``GoogleV3``, but no geocoder could be found.
    """
